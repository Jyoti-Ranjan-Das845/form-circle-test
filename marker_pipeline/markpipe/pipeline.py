"""The two stages, kept separate so any number of readers can be tried on one detection run:

    detect_pages()  pairs -> <out>/<page>/{markers.json, overlay.png, ink_only.png, crops/marker_NN_<kind>.png}
                    and <out>/summary.json
    read_crops()    <out>/*/markers.json + a reader -> <out>/reads/<reader>/<mode>.json

Input modes for reading (which crops go to the reader, with which instruction):
    marked  the marked crop; the reader must find the circle itself (the realistic setting)
    inside  only the circle's interior, from the clean page
    clean   the whole window from the clean page
    both    marked + clean crop together (multi-image readers only)
"""
import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import crops as C
from .config import DetectorConfig
from .detect import PageMismatchError, detect
from .imaging import load_rgb, save_rgb

log = logging.getLogger(__name__)

CIRCLE_PROMPT = "What text is inside the red circle? Reply with only that text, exactly as printed."
PLAIN_PROMPT = "What text is in this image? Reply with only the text, exactly as printed."
BOTH_PROMPT = ("Image 1 is a crop of a page with a pen circle on it. Image 2 is the same crop without the circle. "
               "What text is inside the circle? Reply with only that text, exactly as printed.")
MODES = {
    "marked": (("marked",), CIRCLE_PROMPT),
    "inside": (("inside",), PLAIN_PROMPT),
    "clean": (("clean",), PLAIN_PROMPT),
    "both": (("marked", "clean"), BOTH_PROMPT),
}


@dataclass
class PageResult:
    page: str
    status: str                       # "ok", "unmarked" or "error"
    markers: list = field(default_factory=list)
    error: str = ""

    def summary(self):
        out = {"page": self.page, "status": self.status, "markers": len(self.markers)}
        if self.markers:
            out["closed"] = sum(m["shape"] == "closed" for m in self.markers)
            out["flagged"] = [f"{m['id']}:{m['shape']}:{m['note']}" for m in self.markers
                              if m["shape"] != "closed" or m["note"]]
        if self.error:
            out["error"] = self.error
        return out


def detect_page(pair, out_dir, cfg=DetectorConfig()):
    """Detect, crop and save one page pair. Problems with the input are reported in the result, not raised."""
    page_dir = Path(out_dir) / pair.page
    try:
        clean, marked = load_rgb(pair.clean), load_rgb(pair.marked)
        ink, markers = detect(clean, marked, cfg)
    except (OSError, PageMismatchError) as e:
        log.error("%s: %s", pair.page, e)
        return PageResult(pair.page, "error", error=str(e))

    records, boxes = [], []
    for m in markers:
        cut = C.make_crops(m, clean, marked, cfg)
        record = m.to_dict() | {"crop_box": list(cut.box)}
        for kind in C.KINDS:
            record[f"crop_{kind}"] = None
        for kind, image in cut.items():
            name = f"crops/marker_{m.id:02d}_{kind}.png"
            save_rgb(image, page_dir / name)
            record[f"crop_{kind}"] = name
        records.append(record)
        boxes.append(cut.box)

    page_dir.mkdir(parents=True, exist_ok=True)
    save_rgb(C.overlay(marked, markers, boxes), page_dir / "overlay.png")
    save_rgb(C.ink_only(ink, marked), page_dir / "ink_only.png")
    meta = {"page": pair.page, "marked": str(pair.marked), "clean": str(pair.clean),
            "size": [int(marked.shape[1]), int(marked.shape[0])], "config": cfg.to_dict(), "markers": records}
    (page_dir / "markers.json").write_text(json.dumps(meta, indent=1))
    return PageResult(pair.page, "ok" if records else "unmarked", records)


def detect_pages(pairs, out_dir, cfg=DetectorConfig()):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for pair in pairs:
        r = detect_page(pair, out_dir, cfg)
        log.info("%s: %s, %d marker(s)", r.page, r.status, len(r.markers))
        results.append(r)
    (out_dir / "summary.json").write_text(json.dumps([r.summary() for r in results], indent=1))
    return results


def reader_slug(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name.split("/")[-1]).strip("_") or "reader"


def read_crops(out_dir, reader, modes=("marked",), pages=None):
    """Ask `reader` about every crop of a previous detect run. Returns {mode: [row, ...]} and saves one JSON per
    mode. A failing crop is recorded with its error and the run continues."""
    out_dir = Path(out_dir)
    metas = [json.loads(p.read_text()) for p in sorted(out_dir.glob("*/markers.json"))]
    if pages:
        metas = [m for m in metas if m["page"] in set(pages)]
    if not metas:
        raise FileNotFoundError(f"no markers.json under {out_dir}; run detection first")
    save_dir = out_dir / "reads" / reader_slug(reader.name)
    save_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for mode in modes:
        if mode not in MODES:
            raise ValueError(f"unknown mode {mode!r}; choose from {', '.join(MODES)}")
        kinds, prompt = MODES[mode]
        if len(kinds) > reader.max_images:
            log.warning("%s takes %d image(s); mode %r needs %d, skipped", reader.name, reader.max_images, mode, len(kinds))
            continue
        if mode in ("marked", "both") and not reader.follows_instructions:
            log.warning("%s takes no instruction, so on %r crops it transcribes everything in the window", reader.name, mode)
        rows = []
        for meta in metas:
            page_dir = out_dir / meta["page"]
            for m in meta["markers"]:
                paths = [m.get(f"crop_{k}") for k in kinds]
                row = {"page": meta["page"], "id": m["id"], "mode": mode, "answer": None, "seconds": 0.0, "error": None}
                if not all(paths):
                    row["error"] = f"no {'/'.join(kinds)} crop (open mark)"
                else:
                    t0 = time.time()
                    try:
                        row["answer"] = reader.read([page_dir / p for p in paths], prompt)
                    except Exception as e:  # one bad crop or model hiccup must not lose the whole run
                        row["error"] = f"{type(e).__name__}: {e}"
                    row["seconds"] = round(time.time() - t0, 2)
                log.info("[%s] %s #%d: %r%s", mode, meta["page"], m["id"], row["answer"],
                         f"  ERROR {row['error']}" if row["error"] else "")
                rows.append(row)
        (save_dir / f"{mode}.json").write_text(json.dumps({"reader": reader.name, "mode": mode, "rows": rows}, indent=1))
        results[mode] = rows
    return results
