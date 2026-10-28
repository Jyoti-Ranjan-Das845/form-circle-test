"""Diagnostic only (cheats): shared OCR + mapper, given the TRUE pen strokes (marked page minus clean page).

Its score is the ceiling for every OCR-based pipeline: whatever it misses is lost to OCR or the mapper,
not to finding the circle.
"""
import numpy as np
from PIL import Image, ImageChops

from formeval import data
from pipelines.common import mapper, ocr


def true_marks(page_id):
    import cv2

    name = data.load_truth(page_id)["image"]
    clean = Image.open(data.CLEAN_DIR / name).convert("RGB")
    marked = Image.open(data.MARKED_DIR / name).convert("RGB").resize(clean.size)
    mask = np.array(ImageChops.difference(clean, marked).convert("L")) > 60
    joined = cv2.dilate(mask.astype(np.uint8) * 255, np.ones((7, 7), np.uint8))
    n, labels = cv2.connectedComponents(joined)
    hulls = []
    for k in range(1, n):
        ys, xs = np.nonzero((labels == k) & mask)
        if len(xs) > 10:
            hulls.append(cv2.convexHull(np.stack([xs, ys], 1).astype(np.int32)).reshape(-1, 2).tolist())
    return mask, hulls


def run(task):
    mask, hulls = true_marks(task["page_id"])
    page = ocr.read_without(task["image_path"], mask, grow=1)
    groups = [mapper.words_in_polygon(page, h) for h in hulls]
    return mapper.answer(task, page, [g for g in groups if g])
