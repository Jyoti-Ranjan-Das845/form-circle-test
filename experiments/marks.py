"""Shared helpers for experiments: where the hand-drawn marks really are on a marked page."""
import numpy as np
from PIL import Image, ImageChops, ImageFilter


def circle_boxes(clean_path, marked_path):
    """Boxes around each hand-drawn mark: pixels that differ from the clean page, grouped."""
    a = Image.open(clean_path).convert("RGB")
    b = Image.open(marked_path).convert("RGB")
    diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 60 else 0)
    diff = diff.filter(ImageFilter.MaxFilter(7))  # join the strokes of one circle
    mask = np.array(diff) > 0
    boxes, seen = [], np.zeros_like(mask)
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys, xs):
        if seen[y, x]:
            continue
        stack, pts = [(y, x)], []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop()
            pts.append((cx, cy))
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        p = np.array(pts)
        boxes.append([int(p[:, 0].min()), int(p[:, 1].min()), int(p[:, 0].max()), int(p[:, 1].max())])
    return sorted(boxes, key=lambda bx: (bx[1], bx[0]))


def overlap(inner, outer):
    """Fraction of `inner`'s area that lies inside `outer`."""
    x1, y1 = max(inner[0], outer[0]), max(inner[1], outer[1])
    x2, y2 = min(inner[2], outer[2]), min(inner[3], outer[3])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    area = (inner[2] - inner[0]) * (inner[3] - inner[1])
    return (x2 - x1) * (y2 - y1) / area if area else 0.0


def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0
