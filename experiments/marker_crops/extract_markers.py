"""Deterministic marker detector: marked page minus clean page -> one box + crops per pen mark.

For every page in real_forms_marked/ that differs from real_forms/:
  1. composite RGBA over white, subtract clean, keep pixels that changed (colour-agnostic)
  2. close small stroke gaps, group ink into markers with a dilation of GAP px
  3. per marker: tight box from the *undilated* ink, area, colour, hole count
  4. crop the box (+PAD px) from the marked page and the clean page
Outputs experiments/marker_crops/out/<page>/{markers.json, ink_only.png, overlay.png, crops/}
and experiments/marker_crops/out/summary.json.  No model is involved.

usage: python experiments/marker_crops/extract_markers.py [--gap 8] [--pad 6] [--min-area 40] [--diff-thresh 30]
"""
import argparse, json, os, sys
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
CLEAN, MARKED = ROOT / "real_forms", ROOT / "real_forms_marked"
OUT = Path(__file__).resolve().parent / "out"
GT = ROOT / "data" / "ground_truth"

def load_rgb(p):
    im = Image.open(p)
    if im.mode == "RGBA":                      # edge case: alpha -> flatten on white
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    return np.array(im.convert("RGB"))

def gt_count(stem):
    f = GT / f"{stem[:2]}.json"
    if not f.exists(): return None
    j = json.loads(f.read_text())
    return len(j.get("items") or j.get("answers") or [])

INTERIORS = []

def link_endpoints(sub, max_dist):
    """draw straight bridges between free stroke ends closer than max_dist (greedy nearest pairs)"""
    from skimage.morphology import skeletonize
    sk = skeletonize(sub.astype(bool)).astype(np.uint8)
    nb = cv2.filter2D(sk, -1, np.ones((3, 3), np.float32), borderType=cv2.BORDER_CONSTANT) - sk
    ey, ex = np.where((sk == 1) & (nb == 1))                        # skeleton pixels with exactly one neighbour
    pts = list(zip(ex.tolist(), ey.tolist())); out = sub.copy(); used = set()
    pairs = sorted(((np.hypot(p[0] - q[0], p[1] - q[1]), i, j) for i, p in enumerate(pts) for j, q in enumerate(pts) if i < j))
    for d, i, j in pairs:
        if d > max_dist: break
        if i in used or j in used: continue
        cv2.line(out, pts[i], pts[j], 1, 2); used.update((i, j))
    return out

def holes_of(mask_sub, k3):
    """enclosed regions of a (possibly gap-bridged) stroke mask; returns list of (label_img, stats_row)"""
    nh, hl, hs, _ = cv2.connectedComponentsWithStats(1 - mask_sub, connectivity=4)
    H, W = mask_sub.shape; out = []
    for j in range(1, nh):
        x, y, w, h, area = hs[j]
        if x == 0 or y == 0 or x + w == W or y + h == H: continue   # touches border -> outside, not a hole
        if area >= 25: out.append((j, (int(x), int(y), int(w), int(h), int(area))))
    return hl, out

def describe(ys, xs, marked, interior_full, shape, note):
    x1, y1, x2, y2 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    px = marked[ys, xs].astype(int); r, g, b = px[:, 0], px[:, 1], px[:, 2]
    INTERIORS.append(interior_full)
    return dict(x1=x1, y1=y1, x2=x2, y2=y2, w=x2 - x1 + 1, h=y2 - y1 + 1, ink_px=int(len(xs)),
                red_fraction=round(float(((r - g > 40) & (r - b > 40)).mean()), 3),
                mean_rgb=[int(v) for v in px.mean(axis=0)], shape=shape, note=note)

def split_component(comp, ink, marked, a, k3):
    """One connected ink blob -> one or more markers.
    Holes are found on a gap-bridged copy so a broken stroke still yields an interior.
    nested holes (double loop / enlarged redraw) -> one marker, interior = union of holes.
    side-by-side holes (two circles touching)   -> one marker per hole, box = that hole grown by the stroke width.
    no hole (tick, underline, mostly-missing arc) -> one open marker, no interior."""
    ys, xs = np.where(comp)
    x1, y1, x2, y2 = xs.min(), ys.min(), xs.max(), ys.max()
    pad = a.gap + 2
    sub = np.zeros((y2 - y1 + 1 + 2 * pad, x2 - x1 + 1 + 2 * pad), np.uint8)
    sub[ys - y1 + pad, xs - x1 + pad] = 1
    # gap bridging by endpoint linking: skeletonise the stroke, find its free ends, and draw a line between
    # any two ends closer than 2*gap px. Unlike a big morphological close this never fills a small interior.
    bridged = link_endpoints(sub, 2 * a.gap)
    k1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    hl, holes = holes_of(cv2.morphologyEx(bridged, cv2.MORPH_CLOSE, k1), k3)
    def to_full(mask_sub):
        f = np.zeros(ink.shape, np.uint8)
        f[y1 - pad:y2 + 1 + pad, x1 - pad:x2 + 1 + pad][:mask_sub.shape[0], :mask_sub.shape[1]] = mask_sub[:f[y1 - pad:y2 + 1 + pad, x1 - pad:x2 + 1 + pad].shape[0], :f[y1 - pad:y2 + 1 + pad, x1 - pad:x2 + 1 + pad].shape[1]]
        return f
    if not holes:
        return [describe(ys, xs, marked, np.zeros(ink.shape, np.uint8), "open", "no enclosed interior")]
    if len(holes) == 1:
        return [describe(ys, xs, marked, to_full((hl == holes[0][0]).astype(np.uint8)), "closed", "")]
    # several holes. A hole is "thin" if no point in it is farther than THIN px from the stroke (distance
    # transform), which catches ring pieces of a double loop and the lens of two overlapping circles even when
    # they are crescent-shaped. Thin holes attach to the fat interior they touch; fat interiors stay separate.
    # Finally a cluster whose combined box encloses another cluster's box swallows it (wide redraw ring).
    THIN = 4
    dtv = {j: float(cv2.distanceTransform((hl == j).astype(np.uint8), cv2.DIST_L2, 3).max()) for j, _ in holes}
    thin = lambda h: dtv[h[0]] <= THIN
    def near(A, B, t=4):
        ax, ay, aw, ah, _ = A; bx, by, bw, bh, _ = B
        return ax < bx + bw + t and bx < ax + aw + t and ay < by + bh + t and by < ay + ah + t
    clusters = [[h] for h in holes if not thin(h)]
    for h in holes:
        if not thin(h): continue
        cands = [c for c in clusters if any(near(h[1], b2) for _, b2 in c)]
        if cands: cands[0].append(h)
        else: clusters.append([h])
    def ubox(c):
        xs_ = [b[0] for _, b in c]; ys_ = [b[1] for _, b in c]
        return (min(xs_), min(ys_), max(b[0] + b[2] for _, b in c) - min(xs_), max(b[1] + b[3] for _, b in c) - min(ys_), 0)
    def encloses(A, B, t=2):
        ax, ay, aw, ah, _ = A; bx, by, bw, bh, _ = B
        return ax - t <= bx and ay - t <= by and ax + aw + t >= bx + bw and ay + ah + t >= by + bh
    merged = True
    while merged and len(clusters) > 1:
        merged = False
        for i in range(len(clusters)):
            for j in range(len(clusters)):
                if i != j and encloses(ubox(clusters[i]), ubox(clusters[j])):
                    clusters[i] += clusters.pop(j); merged = True; break
            if merged: break
    if len(clusters) == 1:
        union = np.zeros_like(sub)
        for j, _ in holes: union |= (hl == j).astype(np.uint8)
        return [describe(ys, xs, marked, to_full(union), "closed", f"double stroke, {len(holes)} overlapping holes merged")]
    holes = [(c[0][0], c[0][1]) for c in clusters]                 # one representative hole per cluster
    hl2 = np.zeros_like(hl)
    for k, c in enumerate(clusters, 1):
        for j, _ in c: hl2[hl == j] = k
    hl, holes = hl2, [(k, c[0][1]) for k, c in enumerate(clusters, 1)]
    # side by side: one marker per hole, ink assigned to the nearest hole
    stroke = max(2, int(round(comp.sum() / max(1, cv2.countNonZero(cv2.morphologyEx(sub, cv2.MORPH_ERODE, k3)) + 1))))
    out = []
    dist = {j: cv2.distanceTransform((hl != j).astype(np.uint8), cv2.DIST_L2, 3) for j, _ in holes}
    owner = np.argmin(np.stack([dist[j] for j, _ in holes]), axis=0)
    for k, (j, _) in enumerate(holes):
        sel = (owner == k) & (sub == 1)
        sy, sx = np.where(sel)
        if len(sx) < a.min_area: continue
        out.append(describe(sy + y1 - pad, sx + x1 - pad, marked, to_full((hl == j).astype(np.uint8)),
                            "closed", f"split from a blob of {len(holes)} touching circles"))
    return out

def detect(clean, marked, a):
    INTERIORS.clear()
    d = np.abs(marked.astype(int) - clean.astype(int)).max(axis=2)
    ink = (d > a.diff_thresh).astype(np.uint8)              # 1 = pen pixel
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    globals()['K3'] = k3
    ink = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, k3)        # heal 1-px anti-alias holes
    kg = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * a.gap + 1, 2 * a.gap + 1))
    groups = cv2.dilate(ink, kg)                            # bridge stroke gaps <= 2*gap px
    n, lab = cv2.connectedComponents(groups, connectivity=8)
    markers = []
    for i in range(1, n):
        comp = (lab == i) & (ink == 1)
        if comp.sum() < a.min_area:                           # edge case: specks
            continue
        for m in split_component(comp, ink, marked, a, k3):
            markers.append(m)
    order = sorted(range(len(markers)), key=lambda i: (markers[i]["y1"] // 40, markers[i]["x1"]))  # reading order
    markers = [markers[i] for i in order]; INTERIORS[:] = [INTERIORS[i] for i in order]
    for i, m in enumerate(markers, 1): m["id"] = i
    return ink, markers

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap", type=int, default=8); ap.add_argument("--pad", type=int, default=6)
    ap.add_argument("--min-area", type=int, default=40); ap.add_argument("--diff-thresh", type=int, default=30)
    ap.add_argument("--pages", default=None, help="comma list of 2-digit page ids")
    a = ap.parse_args()
    summary = []
    for mp in sorted(MARKED.glob("*.png")):
        stem = mp.stem
        if a.pages and stem[:2] not in a.pages.split(","): continue
        cp = CLEAN / mp.name
        if not cp.exists():
            summary.append(dict(page=stem, status="no clean counterpart")); continue
        clean, marked = load_rgb(cp), load_rgb(mp)
        if clean.shape != marked.shape:                      # edge case: size mismatch
            summary.append(dict(page=stem, status=f"size mismatch clean{clean.shape[:2]} marked{marked.shape[:2]}")); continue
        ink, markers = detect(clean, marked, a)
        if not markers:                                      # edge case: placeholder page
            summary.append(dict(page=stem, status="unmarked", markers=0, gt_items=gt_count(stem))); continue
        od = OUT / stem; (od / "crops").mkdir(parents=True, exist_ok=True)
        H, W = ink.shape
        ink_only = np.full((H, W, 3), 255, np.uint8); ink_only[ink == 1] = marked[ink == 1]
        Image.fromarray(ink_only).save(od / "ink_only.png")
        k3 = K3
        ov = Image.fromarray(marked.copy()); dr = ImageDraw.Draw(ov)
        for m in markers:
            x1, y1 = max(0, m["x1"] - a.pad), max(0, m["y1"] - a.pad)
            x2, y2 = min(W, m["x2"] + a.pad + 1), min(H, m["y2"] + a.pad + 1)
            m["crop_box"] = [x1, y1, x2, y2]
            Image.fromarray(marked[y1:y2, x1:x2]).save(od / "crops" / f"marker_{m['id']:02d}_marked.png")
            Image.fromarray(clean[y1:y2, x1:x2]).save(od / "crops" / f"marker_{m['id']:02d}_clean.png")
            m["crop_marked"] = f"crops/marker_{m['id']:02d}_marked.png"; m["crop_clean"] = f"crops/marker_{m['id']:02d}_clean.png"
            inner = INTERIORS[m["id"] - 1][y1:y2, x1:x2]
            if inner.any():
                inner = cv2.dilate(inner, k3, iterations=2)          # keep glyph edges touching the stroke
                io = clean[y1:y2, x1:x2].copy(); io[inner == 0] = 255
                Image.fromarray(io).save(od / "crops" / f"marker_{m['id']:02d}_inside.png")
                m["crop_inside"] = f"crops/marker_{m['id']:02d}_inside.png"
            else:
                m["crop_inside"] = None                               # open stroke: no interior
            col = (0, 160, 0) if m["shape"] == "closed" else ((255, 140, 0) if m["shape"] == "open" else (0, 0, 255))
            dr.rectangle([x1, y1, x2 - 1, y2 - 1], outline=col, width=2)
            dr.text((x1 + 2, max(0, y1 - 12)), str(m["id"]), fill=col)
        ov.save(od / "overlay.png")
        (od / "markers.json").write_text(json.dumps(dict(page=stem, size=[W, H], params=vars(a), markers=markers), indent=1))
        flags = [f"{m['id']}:{m['shape']}:{m['note']}" for m in markers if m["shape"] != "closed" or m["note"]]
        summary.append(dict(page=stem, status="ok", markers=len(markers), gt_items=gt_count(stem),
                            closed=sum(m["shape"] == "closed" for m in markers), flagged_ids=flags,
                            min_red_fraction=min(m["red_fraction"] for m in markers)))
    OUT.mkdir(exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    for s in summary: print(s)

if __name__ == "__main__":
    main()
