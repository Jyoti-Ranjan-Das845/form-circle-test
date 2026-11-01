"""Cut each mark out of the page, and draw review images.

Every mark gets up to three crops of the same window (the mark's box plus cfg.pad px):
    marked  from the marked page, ink included (the only one available in real use)
    clean   the same window from the clean page
    inside  the clean window with everything outside the circle's interior whitened (closed marks only)
"""
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .config import DetectorConfig

KINDS = ("marked", "clean", "inside")
_K3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
_COLOURS = {"closed": (0, 160, 0), "open": (255, 140, 0)}


@dataclass
class Crops:
    box: tuple              # (x1, y1, x2, y2) page window, end-exclusive
    marked: np.ndarray
    clean: np.ndarray
    inside: np.ndarray | None

    def items(self):
        return [(k, getattr(self, k)) for k in KINDS if getattr(self, k) is not None]


def crop_window(marker, page_shape, pad):
    H, W = page_shape[:2]
    x1, y1, x2, y2 = marker.box
    return max(0, x1 - pad), max(0, y1 - pad), min(W, x2 + pad + 1), min(H, y2 + pad + 1)


def make_crops(marker, clean, marked, cfg=DetectorConfig()):
    x1, y1, x2, y2 = box = crop_window(marker, marked.shape, cfg.pad)
    inside = None
    if marker.interior is not None:
        interior = marker.interior.window(x1, y1, x2, y2).astype(np.uint8)
        if interior.any():
            interior = cv2.dilate(interior, _K3, iterations=2)  # keep letters that touch the stroke
            inside = clean[y1:y2, x1:x2].copy()
            inside[interior == 0] = 255
    return Crops(box, marked[y1:y2, x1:x2].copy(), clean[y1:y2, x1:x2].copy(), inside)


def ink_only(ink, marked):
    """The pen ink on a white page."""
    out = np.full(marked.shape, 255, np.uint8)
    out[ink == 1] = marked[ink == 1]
    return out


def overlay(marked, markers, boxes):
    """The marked page with each mark's crop window outlined (green = closed, orange = open) and numbered."""
    im = Image.fromarray(marked.copy())
    draw = ImageDraw.Draw(im)
    for m, (x1, y1, x2, y2) in zip(markers, boxes):
        colour = _COLOURS.get(m.shape, (0, 0, 255))
        draw.rectangle([x1, y1, x2 - 1, y2 - 1], outline=colour, width=2)
        draw.text((x1 + 2, max(0, y1 - 12)), str(m.id), fill=colour)
    return np.array(im)
