"""OCR shared by every pipeline: PP-OCRv6 (small) through RapidOCR / ONNX Runtime, with word boxes.

read(image) -> {"size": (w, h),
                "lines": [{"text": str, "box": [x1, y1, x2, y2]}],
                "words": [{"text": str, "box": [x1, y1, x2, y2], "line": int}]}
`image` is a path or a numpy array (BGR or grey).
"""
import numpy as np

_engine = None


def _get():
    global _engine
    if _engine is None:
        from rapidocr import RapidOCR
        _engine = RapidOCR(params={"Global.log_level": "error"})
    return _engine


def _rect(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]


def _split_stacked(word, line_h):
    """A tall, narrow token like '1234' is a vertical column of characters: give each its own box."""
    x1, y1, x2, y2 = word["box"]
    n = len(word["text"])
    if n < 2 or (y2 - y1) < 2.2 * line_h or (y2 - y1) < 1.5 * (x2 - x1):
        return [word]
    step = (y2 - y1) / n
    return [{"text": ch, "box": [x1, int(y1 + k * step), x2, int(y1 + (k + 1) * step)], "line": word["line"],
             "score": word.get("score", 0.0)} for k, ch in enumerate(word["text"])]


def read(image):
    import cv2

    img = cv2.imread(str(image)) if not isinstance(image, np.ndarray) else image
    out = _get()(img, return_word_box=True)
    lines, words = [], []
    for i, (text, poly) in enumerate(zip(out.txts or [], out.boxes if out.boxes is not None else [])):
        lines.append({"text": text, "box": _rect(poly)})
        for wtext, score, wpoly in (out.word_results[i] if out.word_results else []):
            if wtext.strip():
                words.append({"text": wtext.strip(), "box": _rect(wpoly), "line": i, "score": float(score)})
    line_h = float(np.median([w["box"][3] - w["box"][1] for w in words])) if words else 15.0
    words = [piece for w in words for piece in _split_stacked(w, line_h)]
    return {"size": (img.shape[1], img.shape[0]), "lines": lines, "words": words}


def read_without(image_path, stroke_mask, grow=1):
    """OCR again after painting the given pen-stroke pixels white, so marks don't turn into stray letters."""
    import cv2

    img = cv2.imread(str(image_path))
    mask = stroke_mask.astype(np.uint8) * 255
    if grow:
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=grow)
    img[mask > 0] = 255
    return read(img)


def _iou(a, b):
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


def best_reading(after, before):
    """For each word of the re-read page, keep the more confident reading from before/after erasing marks."""
    for w in after["words"]:
        twin = max(before["words"], key=lambda b: _iou(b["box"], w["box"]), default=None)
        if twin is not None and _iou(twin["box"], w["box"]) > 0.6 and twin.get("score", 0) > w.get("score", 0):
            w["text"] = twin["text"]
    return after
