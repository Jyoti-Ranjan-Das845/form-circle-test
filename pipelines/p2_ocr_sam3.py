"""P2  OCR + vision foundation model: SAM 3 segments "hand-drawn circle"; OCR words inside each mask's outline
are the answer. The pen stroke is erased and the page re-read (same step as P1) so marks don't become letters.

Confidence cut-off 0.2 chosen on the practice set (37/40 circles, 6 false detections), not on the test pages.
SAM 3 runs through the MLX port (github.com/Deekshith-Dade/mlx_sam3, needs Python 3.13):
    .venv_sam3/bin/python -m formeval.run --pipeline pipelines/p2_ocr_sam3.py --ink black
"""
import numpy as np
from PIL import Image

from pipelines.common import mapper, ocr

PROMPT = "hand-drawn circle"
THRESHOLD = 0.2
_proc = None


def _processor():
    global _proc
    if _proc is None:
        from sam3 import build_sam3_image_model
        from sam3.model.sam3_image_processor import Sam3Processor
        _proc = Sam3Processor(build_sam3_image_model(), confidence_threshold=THRESHOLD)
    return _proc


def _stroke(mask):
    """The pen line itself: the mask if it is a thin ring, or the rim of the mask if SAM filled the loop."""
    import cv2

    ys, xs = np.nonzero(mask)
    hull = cv2.convexHull(np.stack([xs, ys], 1).astype(np.int32))
    if mask.sum() / max(1.0, cv2.contourArea(hull)) < 0.5:
        return mask
    return mask & ~(cv2.erode(mask.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)


def run(task):
    import cv2

    path = task["image_path"]
    first = ocr.read(path)
    proc = _processor()
    state = proc.set_text_prompt(PROMPT, proc.set_image(Image.open(path).convert("RGB")))
    hulls, strokes = [], np.zeros((first["size"][1], first["size"][0]), dtype=bool)
    for mask in np.array(state.get("masks", [])):
        m = np.squeeze(mask) > 0
        if m.shape != strokes.shape or m.sum() < 10:
            continue
        ys, xs = np.nonzero(m)
        hulls.append(cv2.convexHull(np.stack([xs, ys], 1).astype(np.int32)).reshape(-1, 2).tolist())
        strokes |= _stroke(m)
    page = ocr.best_reading(ocr.read_without(path, strokes), first) if hulls else first
    groups = []
    for hull in hulls:
        ids = mapper.words_in_polygon(page, hull, min_inside=0.5)
        if ids and len(ids) <= 15 and ids not in groups:
            groups.append(ids)
    return mapper.answer(task, page, groups)
