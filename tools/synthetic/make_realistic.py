"""Turn clean form renders into realistic phone photos or office scans, keeping the answer boxes aligned.

Every geometric step (paper curl, perspective, rotation) is applied to the option boxes as well,
so the answer key still points at the right pixels in the final image.

Usage:  .venv/bin/python src/make_realistic.py --clean build/clean --gt build/ground_truth \
            --out form_images --key answer_key
        (--style photo|scan forces one look; default mixes them)
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from augraphy import AugraphyPipeline, BrightnessTexturize, InkBleed, LowInkRandomLines, NoiseTexturize

SCAN_FORMS = {"04_employee_survey", "08_vintage_product_test", "10_vehicle_inspection"}


# ----------------------------------------------------------------------------- helpers
def gauss_field(h, w, rng, n=4, lo=0.8, hi=1.05):
    """Smooth random illumination field in [lo, hi]."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    f = np.zeros((h, w), np.float32)
    for _ in range(n):
        cx, cy = rng.uniform(-0.2, 1.2) * w, rng.uniform(-0.2, 1.2) * h
        s = rng.uniform(0.4, 0.9) * max(h, w)
        f += rng.uniform(0.5, 1.0) * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * s * s))
    f = (f - f.min()) / (np.ptp(f) + 1e-6)
    return lo + (hi - lo) * f


def background(h, w, rng):
    kind = rng.choice(["wood", "desk", "fabric", "stone"])
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    if kind == "wood":
        base = np.array(rng.choice([[60, 95, 140], [40, 70, 110], [85, 120, 160]]), np.float32)  # BGR browns
        warp = cv2.GaussianBlur(rng.normal(0, 1, (h // 8, w // 8)).astype(np.float32), (0, 0), 6)
        warp = cv2.resize(warp, (w, h)) * 6
        grain = np.sin((xx * rng.uniform(0.02, 0.04)) + warp) * 0.5 + 0.5
        tone = 0.75 + 0.3 * grain[..., None]
        img = base * tone
    elif kind == "desk":
        base = np.array(rng.choice([[200, 200, 198], [70, 70, 72], [180, 190, 200]]), np.float32)
        img = np.ones((h, w, 3), np.float32) * base
    elif kind == "fabric":
        base = np.array(rng.choice([[120, 80, 50], [70, 90, 60], [110, 110, 120]]), np.float32)
        weave = (np.sin(xx * 0.9) * np.sin(yy * 0.9)) * 0.06 + 1
        img = base * weave[..., None]
    else:
        base = np.array(rng.choice([[150, 150, 150], [210, 205, 200]]), np.float32)
        speck = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 1.5) * 18
        img = base + speck[..., None]
    img += rng.normal(0, 4, (h, w, 3)).astype(np.float32)
    img *= gauss_field(h, w, rng, 3, 0.7, 1.05)[..., None]
    return np.clip(img, 0, 255)


def paper_texture(page, rng):
    """Ink bleed, paper fibres and slight uneven brightness via Augraphy (no geometry changes)."""
    pipe = AugraphyPipeline(
        ink_phase=[InkBleed(intensity_range=(0.1, 0.3), kernel_size=(3, 3), severity=(0.2, 0.4), p=0.6)],
        paper_phase=[NoiseTexturize(sigma_range=(1, 2), turbulence_range=(2, 3), p=0.6),
                     BrightnessTexturize(texturize_range=(0.96, 0.995), deviation=0.02, p=0.7)],
        post_phase=[], random_seed=int(rng.integers(1 << 30)))
    return pipe(page)


def curl(page, pts, rng):
    """Gentle paper bend: vertical shift that varies with x, then horizontal shift that varies with y.
    Each pass shifts along one axis as a function of the other, so the point mapping is exact."""
    h, w = page.shape[:2]
    out = page
    shade = np.ones((h, w), np.float32)
    for axis in (0, 1):
        n = w if axis == 0 else h
        amp = rng.uniform(0.0015, 0.0045) * (h if axis == 0 else w)
        freq, ph = rng.uniform(0.5, 1.4), rng.uniform(0, np.pi * 2)
        t = np.arange(n, dtype=np.float32)
        d = amp * np.sin(np.pi * freq * t / n + ph)
        slope = np.gradient(d)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        if axis == 0:   # dest (x,y) samples src (x, y + d[x])
            mx, my = xx, yy + d[None, :]
            pts[:, 1] -= np.interp(pts[:, 0], t, d)
            shade *= (1 + 6.0 * slope)[None, :]
        else:           # dest (x,y) samples src (x + d[y], y)
            mx, my = xx + d[:, None], yy
            pts[:, 0] -= np.interp(pts[:, 1], t, d)
            shade *= (1 + 6.0 * slope)[:, None]
        out = cv2.remap(out, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return np.clip(out.astype(np.float32) * np.clip(shade, 0.85, 1.1)[..., None], 0, 255).astype(np.uint8), pts


def finish(img, rng, blur=(0.5, 1.3), noise=(2, 5), q=(72, 90)):
    s = rng.uniform(*blur)
    img = cv2.GaussianBlur(img, (0, 0), s)
    if rng.random() < 0.25:  # slight hand shake
        k = int(rng.integers(3, 7))
        ker = np.zeros((k, k), np.float32)
        ker[k // 2, :] = 1 / k
        M = cv2.getRotationMatrix2D((k / 2, k / 2), rng.uniform(0, 180), 1)
        img = cv2.filter2D(img, -1, cv2.warpAffine(ker, M, (k, k)))
    img = img.astype(np.float32) + rng.normal(0, rng.uniform(*noise), img.shape).astype(np.float32)
    ok, buf = cv2.imencode(".jpg", np.clip(img, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(*q))])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR), buf


# ----------------------------------------------------------------------------- styles
def phone_photo(page, pts, rng):
    page = paper_texture(page, rng)
    page, pts = curl(page, pts, rng)
    ph, pw = page.shape[:2]

    W, H = 2268, 3024  # 3:4 phone frame
    bg = background(H, W, rng)
    fill = rng.uniform(0.80, 0.93)
    sc = min(W / pw, H / ph) * fill
    cw, ch = pw * sc, ph * sc
    cx, cy = W / 2 + rng.uniform(-0.04, 0.04) * W, H / 2 + rng.uniform(-0.03, 0.03) * H
    ang = np.deg2rad(rng.uniform(-2.5, 2.5))
    corners = np.array([[-cw / 2, -ch / 2], [cw / 2, -ch / 2], [cw / 2, ch / 2], [-cw / 2, ch / 2]])
    R = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
    dst = corners @ R.T + [cx, cy]
    # keystone: camera not perfectly above the page
    tilt_x, tilt_y = rng.uniform(-0.05, 0.05), rng.uniform(-0.06, 0.06)
    dst[0] += [tilt_y * cw * 0.5 + rng.normal(0, 0.008) * cw, rng.normal(0, 0.008) * ch]
    dst[1] += [-tilt_y * cw * 0.5 + rng.normal(0, 0.008) * cw, rng.normal(0, 0.008) * ch]
    dst[1] += [0, tilt_x * ch * 0.5]
    dst[2] += [0, -tilt_x * ch * 0.5]
    src = np.array([[0, 0], [pw, 0], [pw, ph], [0, ph]], np.float32)
    M = cv2.getPerspectiveTransform(src, dst.astype(np.float32))

    warped = cv2.warpPerspective(page, M, (W, H), flags=cv2.INTER_AREA)
    mask = cv2.warpPerspective(np.full((ph, pw), 255, np.uint8), M, (W, H), flags=cv2.INTER_AREA).astype(np.float32) / 255
    # soft shadow of the sheet on the surface
    sh = cv2.GaussianBlur(np.roll(mask, (int(rng.integers(6, 20)), int(rng.integers(4, 16))), (0, 1)), (0, 0), 14)
    bg *= (1 - 0.35 * sh)[..., None]
    img = warped.astype(np.float32) * mask[..., None] + bg * (1 - mask[..., None])

    # room lighting + optional shadow from the phone / hand
    img *= gauss_field(H, W, rng, 4, rng.uniform(0.72, 0.88), 1.04)[..., None]
    if rng.random() < 0.65:
        poly = np.zeros((H, W), np.float32)
        side = rng.integers(4)
        a, b = sorted(rng.uniform(0, 1, 2))
        depth = rng.uniform(0.15, 0.45)
        if side == 0:
            p = [[a * W, 0], [b * W, 0], [b * W + rng.uniform(-200, 200), depth * H], [a * W + rng.uniform(-200, 200), depth * H * rng.uniform(0.6, 1)]]
        elif side == 1:
            p = [[W, a * H], [W, b * H], [W - depth * W, b * H], [W - depth * W * rng.uniform(0.6, 1), a * H]]
        elif side == 2:
            p = [[a * W, H], [b * W, H], [b * W, H - depth * H], [a * W, H - depth * H * rng.uniform(0.6, 1)]]
        else:
            p = [[0, a * H], [0, b * H], [depth * W, b * H], [depth * W * rng.uniform(0.6, 1), a * H]]
        cv2.fillPoly(poly, [np.array(p, np.int32)], 1.0)
        poly = cv2.GaussianBlur(poly, (0, 0), rng.uniform(50, 120))
        img *= (1 - rng.uniform(0.18, 0.38) * poly)[..., None]
    # white balance, vignette
    img *= np.array(rng.choice([[0.92, 1.0, 1.06], [1.04, 1.0, 0.95], [0.98, 1.0, 1.01]]), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r2 = ((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2
    img *= (1 - rng.uniform(0.15, 0.35) * r2)[..., None]

    pts = cv2.perspectiveTransform(pts.reshape(-1, 1, 2).astype(np.float32), M).reshape(-1, 2)
    out, buf = finish(np.clip(img, 0, 255).astype(np.uint8), rng)
    return out, buf, pts


def office_scan(page, pts, rng):
    page = paper_texture(page, rng)
    if rng.random() < 0.7:
        page = AugraphyPipeline(ink_phase=[LowInkRandomLines(count_range=(3, 10), use_consistent_lines=False, p=1)],
                                paper_phase=[], post_phase=[], random_seed=int(rng.integers(1 << 30)))(page)
    h, w = page.shape[:2]
    gray = rng.random() < 0.6
    ang = rng.uniform(-1.4, 1.4)
    M = cv2.getRotationMatrix2D((w / 2 + rng.uniform(-20, 20), h / 2 + rng.uniform(-20, 20)), ang, rng.uniform(0.97, 1.0))
    M[:, 2] += rng.uniform(-25, 25, 2)
    img = cv2.warpAffine(page, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(250, 250, 250))
    img = img.astype(np.float32)
    img *= gauss_field(h, w, rng, 2, 0.94, 1.0)[..., None]
    img = np.clip((img - 128) * rng.uniform(1.05, 1.25) + 128 + rng.uniform(0, 12), 0, 255)
    # dust specks from the scanner glass
    for _ in range(int(rng.integers(20, 90))):
        cv2.circle(img, (int(rng.integers(w)), int(rng.integers(h))), int(rng.integers(1, 4)), (40, 40, 40), -1)
    if gray:
        img = cv2.cvtColor(cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    img = cv2.resize(img.astype(np.uint8), (1700, 2200), interpolation=cv2.INTER_AREA)  # 200 dpi
    pts = np.hstack([pts, np.ones((len(pts), 1))]) @ M.T * (1700 / w)
    out, buf = finish(img, rng, blur=(0.3, 0.7), noise=(1, 3), q=(80, 92))
    return out, buf, pts


# ----------------------------------------------------------------------------- main
def boxes_to_pts(gt):
    pts, index = [], []
    for qi, q in enumerate(gt["questions"]):
        for key, b in [("region", q["region"])] + [(oi, o["box"]) for oi, o in enumerate(q["options"])]:
            x1, y1, x2, y2 = b
            pts += [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            index.append((qi, key))
    return np.array(pts, np.float32), index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", default="build/clean")
    ap.add_argument("--gt", default="build/ground_truth")
    ap.add_argument("--out", default="form_images")
    ap.add_argument("--key", default="answer_key")
    ap.add_argument("--style", choices=["photo", "scan"])
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    out, key = Path(args.out), Path(args.key)
    out.mkdir(parents=True, exist_ok=True)
    key.mkdir(parents=True, exist_ok=True)

    for k, gt_path in enumerate(sorted(Path(args.gt).glob("*.json"))):
        gt = json.loads(gt_path.read_text())
        fid = gt["form_id"]
        rng = np.random.default_rng(args.seed * 1000 + k)
        page = cv2.imread(str(Path(args.clean) / f"{fid}.png"))
        style = args.style or ("scan" if fid in SCAN_FORMS else "photo")
        page = cv2.resize(page, (1900, 2459), interpolation=cv2.INTER_AREA) if style == "photo" else page
        pts, index = boxes_to_pts(gt)
        pts *= page.shape[1] / gt["width"]
        img, buf, pts = (phone_photo if style == "photo" else office_scan)(page, pts, rng)

        name = f"{fid}.jpg"
        (out / name).write_bytes(buf.tobytes())
        quads = pts.reshape(-1, 4, 2)
        for (qi, which), quad in zip(index, quads):
            box = [int(quad[:, 0].min()), int(quad[:, 1].min()), int(np.ceil(quad[:, 0].max())), int(np.ceil(quad[:, 1].max()))]
            entry = {"box": box, "quad": np.round(quad).astype(int).tolist()}
            if which == "region":
                gt["questions"][qi]["region"] = box
            else:
                gt["questions"][qi]["options"][which].update(entry)
        gt.update({"image": f"{out.name}/{name}", "width": img.shape[1], "height": img.shape[0], "style": style,
                   "box_format": "box = x1,y1,x2,y2; quad = 4 corners (clockwise from top-left), in image pixels"})
        (key / f"{fid}.json").write_text(json.dumps(gt, indent=1))
        print(f"{name}: {style} {img.shape[1]}x{img.shape[0]}")


if __name__ == "__main__":
    main()
