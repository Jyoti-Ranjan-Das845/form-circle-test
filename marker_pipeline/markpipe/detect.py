"""Find pen marks by comparing a marked page with its clean original. No model is involved.

    ink_mask()      pixels that changed between the two pages (colour-agnostic, so red over black text counts)
    find_markers()  group the ink into marks and classify each one:
                      closed  a circle with an enclosed interior (small breaks in the stroke are bridged)
                      open    no interior: a tick, an underline, or a circle with a large part missing
                    two touching circles are split into two marks; a double loop is kept as one
    detect()        both steps, after checking the pages are comparable
"""
from dataclasses import dataclass, field

import cv2
import numpy as np

from .config import DetectorConfig

_K3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
_K5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))


class PageMismatchError(ValueError):
    """The marked and clean pages cannot be compared pixel by pixel."""


@dataclass
class Region:
    """A boolean mask placed on the page with its top-left corner at (x0, y0); the corner may lie off the page."""
    mask: np.ndarray
    x0: int
    y0: int

    def window(self, x1, y1, x2, y2):
        """The part of the mask inside the page window [x1, x2) x [y1, y2), as an array of that window's size."""
        out = np.zeros((y2 - y1, x2 - x1), bool)
        h, w = self.mask.shape
        ax1, ay1 = max(x1, self.x0), max(y1, self.y0)
        ax2, ay2 = min(x2, self.x0 + w), min(y2, self.y0 + h)
        if ax1 < ax2 and ay1 < ay2:
            out[ay1 - y1:ay2 - y1, ax1 - x1:ax2 - x1] = self.mask[ay1 - self.y0:ay2 - self.y0, ax1 - self.x0:ax2 - self.x0]
        return out


@dataclass
class Marker:
    box: tuple              # (x1, y1, x2, y2), inclusive pixel bounds of the ink
    ink_px: int
    red_fraction: float     # share of the ink that is clearly red
    mean_rgb: list
    shape: str              # "closed" or "open"
    note: str = ""
    interior: Region | None = field(default=None, repr=False)
    id: int = 0

    def to_dict(self):
        x1, y1, x2, y2 = self.box
        return dict(id=self.id, x1=x1, y1=y1, x2=x2, y2=y2, w=x2 - x1 + 1, h=y2 - y1 + 1, ink_px=self.ink_px,
                    red_fraction=self.red_fraction, mean_rgb=self.mean_rgb, shape=self.shape, note=self.note)


def ink_mask(clean, marked, cfg=DetectorConfig()):
    """1 where the marked page differs from the clean one by more than cfg.diff_thresh in any channel."""
    _check_pair(clean, marked)
    diff = np.abs(marked.astype(np.int16) - clean.astype(np.int16)).max(axis=2)
    ink = (diff > cfg.diff_thresh).astype(np.uint8)
    return cv2.morphologyEx(ink, cv2.MORPH_CLOSE, _K3)  # heal 1 px anti-aliasing holes in the stroke


def find_markers(ink, marked, cfg=DetectorConfig()):
    """Marks in reading order (top to bottom in bands of cfg.order_band px, then left to right), ids from 1."""
    grow = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * cfg.gap + 1, 2 * cfg.gap + 1))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(cv2.dilate(ink, grow), connectivity=8)
    markers = []
    for i in range(1, n):
        x, y, w, h = stats[i, :4]
        window = (labels[y:y + h, x:x + w] == i) & (ink[y:y + h, x:x + w] == 1)
        ys, xs = np.nonzero(window)
        if len(xs) < cfg.min_area:  # scanner specks and anti-aliasing leftovers
            continue
        markers += _split_component(ys + y, xs + x, marked, cfg)
    markers.sort(key=lambda m: (m.box[1] // max(cfg.order_band, 1), m.box[0]))
    for k, m in enumerate(markers, 1):
        m.id = k
    return markers


def detect(clean, marked, cfg=DetectorConfig()):
    """(ink mask, markers) for one page pair."""
    ink = ink_mask(clean, marked, cfg)
    return ink, find_markers(ink, marked, cfg)


def _check_pair(clean, marked):
    for name, a in (("clean", clean), ("marked", marked)):
        if a.ndim != 3 or a.shape[2] != 3 or a.dtype != np.uint8:
            raise PageMismatchError(f"{name} page must be an RGB uint8 array, got shape {a.shape} {a.dtype}")
    if clean.shape != marked.shape:
        raise PageMismatchError(f"page sizes differ: clean {clean.shape[1]}x{clean.shape[0]}, "
                                f"marked {marked.shape[1]}x{marked.shape[0]}")


def _describe(ys, xs, marked, shape, note="", interior=None):
    px = marked[ys, xs].astype(int)
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    return Marker(box=(int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), ink_px=int(len(xs)),
                  red_fraction=round(float(((r - g > 40) & (r - b > 40)).mean()), 3),
                  mean_rgb=[int(v) for v in px.mean(axis=0)], shape=shape, note=note, interior=interior)


def _link_endpoints(stroke, max_dist):
    """Join free stroke ends that are closer than max_dist with a straight line (nearest pairs first).
    Unlike a large morphological close, this bridges a broken circle without filling a small interior."""
    from skimage.morphology import skeletonize

    skel = skeletonize(stroke.astype(bool)).astype(np.uint8)
    neighbours = cv2.filter2D(skel, -1, np.ones((3, 3), np.float32), borderType=cv2.BORDER_CONSTANT) - skel
    ey, ex = np.nonzero((skel == 1) & (neighbours == 1))  # skeleton pixels with exactly one neighbour
    ends = list(zip(ex.tolist(), ey.tolist()))
    pairs = sorted((float(np.hypot(p[0] - q[0], p[1] - q[1])), i, j)
                   for i, p in enumerate(ends) for j, q in enumerate(ends) if i < j)
    out, used = stroke.copy(), set()
    for dist, i, j in pairs:
        if dist > max_dist:
            break
        if i not in used and j not in used:
            cv2.line(out, ends[i], ends[j], 1, 2)
            used.update((i, j))
    return out


def _holes(stroke, min_area):
    """Regions enclosed by the stroke: (label image, [(label, (x, y, w, h, area))]). Border-touching = outside."""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(1 - stroke, connectivity=4)
    H, W = stroke.shape
    holes = []
    for j in range(1, n):
        x, y, w, h, area = (int(v) for v in stats[j])
        if x > 0 and y > 0 and x + w < W and y + h < H and area >= min_area:
            holes.append((j, (x, y, w, h, area)))
    return labels, holes


def _near(a, b, tol=4):
    return a[0] < b[0] + b[2] + tol and b[0] < a[0] + a[2] + tol and a[1] < b[1] + b[3] + tol and b[1] < a[1] + a[3] + tol


def _encloses(a, b, tol=2):
    return a[0] - tol <= b[0] and a[1] - tol <= b[1] and a[0] + a[2] + tol >= b[0] + b[2] and a[1] + a[3] + tol >= b[1] + b[3]


def _union_box(cluster):
    x1 = min(b[0] for _, b in cluster)
    y1 = min(b[1] for _, b in cluster)
    return (x1, y1, max(b[0] + b[2] for _, b in cluster) - x1, max(b[1] + b[3] for _, b in cluster) - y1)


def _cluster_holes(labels, holes, thin_hole):
    """Group holes that belong to one circle. A hole is thin when no point in it is farther than thin_hole px from
    the stroke: ring pieces of a double loop, or the lens where two circles overlap. Thin holes join the fat
    interior they touch; fat interiors stay apart. A cluster whose box encloses another's swallows it."""
    width = {j: float(cv2.distanceTransform((labels == j).astype(np.uint8), cv2.DIST_L2, 3).max()) for j, _ in holes}
    clusters = [[h] for h in holes if width[h[0]] > thin_hole]
    for h in holes:
        if width[h[0]] > thin_hole:
            continue
        home = next((c for c in clusters if any(_near(h[1], b) for _, b in c)), None)
        if home is not None:
            home.append(h)
        else:
            clusters.append([h])
    merged = True
    while merged and len(clusters) > 1:
        merged = False
        for i, j in ((i, j) for i in range(len(clusters)) for j in range(len(clusters)) if i != j):
            if _encloses(_union_box(clusters[i]), _union_box(clusters[j])):
                clusters[i] += clusters.pop(j)
                merged = True
                break
    return clusters


def _split_component(ys, xs, marked, cfg):
    """One connected blob of ink -> one or more markers."""
    x1, y1, x2, y2 = xs.min(), ys.min(), xs.max(), ys.max()
    pad = cfg.gap + 2
    ox, oy = int(x1 - pad), int(y1 - pad)  # page position of the local canvas's top-left corner
    stroke = np.zeros((y2 - y1 + 1 + 2 * pad, x2 - x1 + 1 + 2 * pad), np.uint8)
    stroke[ys - oy, xs - ox] = 1

    bridged = cv2.morphologyEx(_link_endpoints(stroke, 2 * cfg.gap), cv2.MORPH_CLOSE, _K5)
    labels, holes = _holes(bridged, cfg.min_hole_area)
    if not holes:
        return [_describe(ys, xs, marked, "open", "no enclosed interior")]
    if len(holes) == 1:
        return [_describe(ys, xs, marked, "closed", interior=Region(labels == holes[0][0], ox, oy))]

    clusters = _cluster_holes(labels, holes, cfg.thin_hole)
    if len(clusters) == 1:  # one circle drawn over twice
        interior = Region(np.isin(labels, [j for j, _ in holes]), ox, oy)
        return [_describe(ys, xs, marked, "closed", f"double stroke, {len(holes)} overlapping holes merged", interior)]

    # Circles side by side: each ink pixel goes to the nearest interior.
    interiors = [np.isin(labels, [j for j, _ in c]) for c in clusters]
    dist = np.stack([cv2.distanceTransform((~m).astype(np.uint8), cv2.DIST_L2, 3) for m in interiors])
    owner = np.argmin(dist, axis=0)
    out = []
    for k, interior in enumerate(interiors):
        sy, sx = np.nonzero((owner == k) & (stroke == 1))
        if len(sx) >= cfg.min_area:
            out.append(_describe(sy + oy, sx + ox, marked, "closed",
                                 f"split from a blob of {len(clusters)} touching circles", Region(interior, ox, oy)))
    return out
