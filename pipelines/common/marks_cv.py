"""Classical mark finder (no model): pen loops are the ink that runs above, below and around words.

Works on grey levels only, so the ink colour never matters. Thresholds are set on the practice set
(tools/practice_eval.py), never on the test pages.

1. ink = dark pixels; erase only the *core band* of every OCR word (its middle half), so a circle's arcs
   above and below a word survive while the letters mostly disappear;
2. drop fragments smaller than a letter, rule lines and page-edge junk; join nearby arcs;
3. a candidate loop must have ink above *and* below the words it encloses (or on 3 of 4 sides),
   and must not be a printed rectangle.
"""
import numpy as np

MIN_FRAG = 0.9   # shortest stroke fragment kept, in text heights
JOIN = 0.6       # gap bridged between arcs of one loop, in text heights


def _text_height(ocr):
    hs = [w["box"][3] - w["box"][1] for w in ocr["words"]]
    return float(np.median(hs)) if hs else 15.0


def _residual(gray, ocr):
    import cv2

    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    core = np.zeros_like(ink)
    for w in ocr["words"]:
        x1, y1, x2, y2 = w["box"]
        q = (y2 - y1) * 0.25
        core[int(y1 + q):int(y2 - q) + 1, x1:x2 + 1] = 255
    return cv2.bitwise_and(ink, cv2.bitwise_not(core))


def candidates(image_path, ocr, loose=False):
    """Stroke groups that might be hand marks: [{"box", "hull", "pixels"}], biggest first."""
    import cv2

    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    h_img, w_img = gray.shape
    th = _text_height(ocr)
    res = _residual(gray, ocr)

    # keep stroke fragments at least ~a letter long; drop dust, letter tops/bottoms, rule lines, edge junk
    n, labels, stats, _ = cv2.connectedComponentsWithStats(res, 8)
    keep = np.zeros_like(res)
    min_len = (0.6 if loose else MIN_FRAG) * th
    for k in range(1, n):
        x, y, w, h, area = stats[k]
        if max(w, h) < min_len or area < 8:
            continue
        if max(w, h) / max(1, min(w, h)) > 25 or w > 0.6 * w_img or h > 0.4 * h_img:
            continue
        if x <= 2 or y <= 2 or x + w >= w_img - 2 or y + h >= h_img - 2:
            continue
        keep[labels == k] = 255

    # join arcs of the same loop (gaps where the loop crossed a word core)
    r = max(2, int(JOIN * th))
    joined = cv2.dilate(keep, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(joined, 8)
    out = []
    for k in range(1, n):
        x, y, w, h, _ = stats[k]
        if h < (0.9 if loose else 1.1) * th or w < (0.9 if loose else 1.1) * th:
            continue
        ys, xs = np.nonzero((labels == k) & (keep > 0))
        if len(xs) < 15:
            continue
        pts = np.stack([xs, ys], axis=1).astype(np.int32)
        hull = cv2.convexHull(pts).reshape(-1, 2)
        bw, bh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        if not loose and cv2.contourArea(hull.astype(np.float32)) / float(bw * bh) > 0.92:
            continue                                     # a printed rectangle, not a hand loop
        out.append({"box": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                    "hull": hull.tolist(), "pixels": pts})
    out.sort(key=lambda c: -(c["box"][2] - c["box"][0]) * (c["box"][3] - c["box"][1]))
    return out


def _surrounds(cand, ocr, word_ids):
    """Ink above and below across a good part of the enclosed words, or on at least 3 of 4 sides."""
    xs = [ocr["words"][i]["box"] for i in word_ids]
    bx1, by1 = min(b[0] for b in xs), min(b[1] for b in xs)
    bx2, by2 = max(b[2] for b in xs), max(b[3] for b in xs)
    p = cand["pixels"]
    midy = (p[:, 1] >= by1) & (p[:, 1] <= by2)
    midx = (p[:, 0] >= bx1) & (p[:, 0] <= bx2)
    width = max(1, bx2 - bx1)
    above = len(np.unique(p[midx & (p[:, 1] < by1 + 3), 0])) / width
    below = len(np.unique(p[midx & (p[:, 1] > by2 - 3), 0])) / width
    left = np.any((p[:, 0] < bx1 + 2) & midy)
    right = np.any((p[:, 0] > bx2 - 2) & midy)
    if above > 0.4 and below > 0.4:
        return True
    return sum([above > 0.2, below > 0.2, left, right]) >= 3


def stroke_mask(shape, cands):
    mask = np.zeros(shape[:2], dtype=bool)
    for c in cands:
        mask[c["pixels"][:, 1], c["pixels"][:, 0]] = True
    return mask


def circled_groups(ocr, cands, max_words=15):
    """Word groups enclosed by a pen loop (ocr should be the re-read page with the strokes erased)."""
    from .mapper import words_in_polygon

    groups = []
    for c in cands:
        ids = words_in_polygon(ocr, c["hull"], min_inside=0.5)
        if 1 <= len(ids) <= max_words and _surrounds(c, ocr, ids):
            groups.append(ids)
    return groups
