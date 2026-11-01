"""Find marked/clean page pairs in a folder.

Naming convention (as in experiment/dataset/ready_to_use):  <page>_marked.<ext>  and  <page>_unmarked.<ext>
e.g. img_01_marked.png + img_01_unmarked.png -> page "img_01".
"""
import logging
import re
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
_NAME = re.compile(r"^(?P<page>.+)_(?P<kind>marked|unmarked)$", re.IGNORECASE)


@dataclass(frozen=True)
class PagePair:
    page: str
    marked: Path
    clean: Path


def find_pairs(folder, pages=None):
    """Pairs sorted by page name. `pages` limits the result to those page names (e.g. ["img_01", "img_20"]).
    Files without a twin are logged and skipped."""
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    found = {}
    for path in sorted(folder.iterdir()):
        m = _NAME.match(path.stem)
        if path.suffix.lower() not in IMAGE_EXTS or not m:
            continue
        kind = m["kind"].lower()
        slot = found.setdefault(m["page"], {})
        if kind in slot:
            raise ValueError(f"two {kind} images for page {m['page']}: {slot[kind].name}, {path.name}")
        slot[kind] = path
    wanted = set(pages) if pages else None
    if wanted:
        missing = wanted - found.keys()
        if missing:
            raise ValueError(f"pages not found in {folder}: {', '.join(sorted(missing))}")
    pairs = []
    for page, slot in sorted(found.items()):
        if wanted and page not in wanted:
            continue
        if "marked" not in slot or "unmarked" not in slot:
            log.warning("page %s has no %s twin, skipped", page, "unmarked" if "marked" in slot else "marked")
            continue
        pairs.append(PagePair(page, slot["marked"], slot["unmarked"]))
    return pairs
