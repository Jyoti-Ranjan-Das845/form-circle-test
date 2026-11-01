"""Detector settings. The defaults are the ones the pipeline was validated with (38/38 marks on the test set)."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DetectorConfig:
    diff_thresh: int = 30       # a pixel is ink when any channel changed by more than this (0-255)
    gap: int = 8                # px; stroke breaks up to 2 * gap are bridged, marks closer than this are grouped
    min_area: int = 40          # ink pixels; smaller blobs are scanner specks
    pad: int = 6                # px of margin around each crop
    min_hole_area: int = 25     # px; enclosed regions smaller than this are not circle interiors
    thin_hole: float = 4.0      # px; a hole no wider than this is a ring piece (double loop), not an interior
    order_band: int = 40        # px; marks whose tops fall in the same band are ordered left to right

    def __post_init__(self):
        for name in ("diff_thresh", "gap", "min_area", "pad", "min_hole_area", "order_band"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be >= 0, got {getattr(self, name)}")
        if not 0 <= self.diff_thresh <= 255:
            raise ValueError(f"diff_thresh must be in 0..255, got {self.diff_thresh}")

    def to_dict(self):
        return asdict(self)
