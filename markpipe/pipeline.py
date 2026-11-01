"""The two stages, kept separate so any number of readers can be tried on one detection run:

    detect_pages()  page pairs -> <out>/<page>/{markers.json, overlay.png, ink_only.png, crops/marker_NN.png}
                    and <out>/summary.json
    read_crops()    <out>/*/markers.json + a reader -> <out>/reads/<reader>.json
"""
import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from .config import DetectorConfig
from .crops import crop_window, ink_only, inside_crop, overlay
from .detect import PageMismatchError, detect
from .imaging import load_rgb, save_rgb

log = logging.getLogger(__name__)

PROMPT = "What text is in this image? Reply with only the text, exactly as printed."


@dataclass
class PageResult:
    page: str
    status: str                       # "ok", "unmarked" or "error"
    markers: list = field(default_factory=list)
    error: str = ""

    def summary(self):
        out = {"page": self.page, "status": self.status, "markers": len(self.markers)}
        if self.markers:
            out["readable"] = sum(m["crop"] is not None for m in self.markers)
            out["flagged"] = [f"{m['id']}:{m['shape']}:{m['note']}" for m in self.markers
                              if m["shape"] != "closed" or m["note"]]
        if self.error:
            out["error"] = self.error
        return out


def detect_page(pair, out_dir, cfg=DetectorConfig()):
    """Detect and crop one page pair. Problems with the input are reported in the result, not raised."""
    page_dir = Path(out_dir) / pair.page
    try:
        clean, marked = load_rgb(pair.clean), load_rgb(pair.marked)
        ink, markers = detect(clean, marked, cfg)
    except (OSError, PageMismatchError) as e:
        log.error("%s: %s", pair.page, e)
        return PageResult(pair.page, "error", error=str(e))

    records = []
    for m in markers:
        record = m.to_dict() | {"crop_box": list(crop_window(m, marked.shape, cfg.pad)), "crop": None}
        crop = inside_crop(m, clean, cfg)
        if crop is not None:
            record["crop"] = f"crops/marker_{m.id:02d}.png"
            save_rgb(crop, page_dir / record["crop"])
        records.append(record)

    page_dir.mkdir(parents=True, exist_ok=True)
    save_rgb(overlay(marked, markers, cfg), page_dir / "overlay.png")
    save_rgb(ink_only(ink, marked), page_dir / "ink_only.png")
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


def read_crops(out_dir, reader, pages=None):
    """Ask `reader` about every crop of a previous detect run. Returns one row per mark and saves them to
    <out>/reads/<reader>.json. A failing crop is recorded with its error and the run continues."""
    out_dir = Path(out_dir)
    metas = [json.loads(p.read_text()) for p in sorted(out_dir.glob("*/markers.json"))]
    if pages:
        metas = [m for m in metas if m["page"] in set(pages)]
    if not metas:
        raise FileNotFoundError(f"no markers.json under {out_dir}; run detection first")
    rows = []
    for meta in metas:
        for m in meta["markers"]:
            row = {"page": meta["page"], "id": m["id"], "answer": None, "seconds": 0.0, "error": None}
            if m["crop"] is None:
                row["error"] = f"{m['shape']} mark, nothing enclosed to read"
            else:
                t0 = time.time()
                try:
                    row["answer"] = reader.read(out_dir / meta["page"] / m["crop"], PROMPT)
                except Exception as e:  # one bad crop or model hiccup must not lose the whole run
                    row["error"] = f"{type(e).__name__}: {e}"
                row["seconds"] = round(time.time() - t0, 2)
            log.info("%s #%d: %r%s", meta["page"], m["id"], row["answer"],
                     f"  ERROR {row['error']}" if row["error"] else "")
            rows.append(row)
    save = out_dir / "reads" / f"{reader_slug(reader.name)}.json"
    save.parent.mkdir(parents=True, exist_ok=True)
    save.write_text(json.dumps({"reader": reader.name, "rows": rows}, indent=1))
    return rows
