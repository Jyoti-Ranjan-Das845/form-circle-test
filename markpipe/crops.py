"""Cut out what each circle encloses, and draw review images.

The inside crop is the mark's window (its box plus cfg.pad px) taken from the clean page, with everything outside
the circle's interior whitened. The reader sees only the circled text: no pen ink, no neighbouring lines.
Open marks (ticks, underlines, circles with a large part missing) enclose nothing and get no crop.
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw

from .config import DetectorConfig

_K3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
_COLOURS = {"closed": (0, 160, 0), "open": (255, 140, 0)}


def crop_window(marker, page_shape, pad):
    """(x1, y1, x2, y2), end-exclusive: the mark's box grown by `pad` and clipped to the page."""
    H, W = page_shape[:2]
    x1, y1, x2, y2 = marker.box
    return max(0, x1 - pad), max(0, y1 - pad), min(W, x2 + pad + 1), min(H, y2 + pad + 1)


def inside_crop(marker, clean, cfg=DetectorConfig()):
    """The clean page inside the circle, white elsewhere; None for a mark that encloses nothing."""
    if marker.interior is None:
        return None
    x1, y1, x2, y2 = crop_window(marker, clean.shape, cfg.pad)
    interior = marker.interior.window(x1, y1, x2, y2).astype(np.uint8)
    if not interior.any():
        return None
    interior = cv2.dilate(interior, _K3, iterations=2)  # keep letters that touch the stroke
    crop = clean[y1:y2, x1:x2].copy()
    crop[interior == 0] = 255
    return crop


def ink_only(ink, marked):
    """The pen ink on a white page."""
    out = np.full(marked.shape, 255, np.uint8)
    out[ink == 1] = marked[ink == 1]
    return out


def overlay(marked, markers, cfg=DetectorConfig()):
    """The marked page with each mark's window outlined (green = closed, orange = open) and numbered."""
    im = Image.fromarray(marked.copy())
    draw = ImageDraw.Draw(im)
    for m in markers:
        x1, y1, x2, y2 = crop_window(m, marked.shape, cfg.pad)
        colour = _COLOURS.get(m.shape, (0, 0, 255))
        draw.rectangle([x1, y1, x2 - 1, y2 - 1], outline=colour, width=2)
        draw.text((x1 + 2, max(0, y1 - 12)), str(m.id), fill=colour)
    return np.array(im)
