"""Docling test 1: does the layout model label a circled option as checkbox_selected?

Usage:  .venv_docling/bin/python experiments/docling/test1_layout.py 20 [heron|egret_large]
Prints every item Docling found with its label and box, and which real circle (marked minus clean) it covers.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments"))
from marks import circle_boxes, overlap  # noqa: E402


def main():
    from docling.datamodel import layout_model_specs as specs
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import LayoutOptions, PdfPipelineOptions
    from docling.document_converter import DocumentConverter, ImageFormatOption

    pid, model = sys.argv[1].zfill(2), (sys.argv[2] if len(sys.argv) > 2 else "heron")
    truth = json.loads((ROOT / "data" / "ground_truth" / f"{pid}.json").read_text())
    marked = ROOT / "real_forms_marked" / truth["image"]
    circles = circle_boxes(ROOT / "real_forms" / truth["image"], marked)

    opts = PdfPipelineOptions()
    opts.layout_options = LayoutOptions(model_spec={"heron": specs.DOCLING_LAYOUT_HERON,
                                                    "egret_large": specs.DOCLING_LAYOUT_EGRET_LARGE}[model])
    conv = DocumentConverter(format_options={InputFormat.IMAGE: ImageFormatOption(pipeline_options=opts)})
    t = time.perf_counter()
    doc = conv.convert(str(marked)).document
    secs = time.perf_counter() - t

    page_h = doc.pages[1].size.height
    items = []
    for item, _ in doc.iterate_items():
        for prov in getattr(item, "prov", []):
            b = prov.bbox.to_top_left_origin(page_h)
            box = [round(b.l), round(b.t), round(b.r), round(b.b)]
            hits = [i + 1 for i, c in enumerate(circles) if overlap(c, box) > 0.3 or overlap(box, c) > 0.5]
            items.append({"label": str(item.label.value if hasattr(item.label, "value") else item.label),
                          "text": getattr(item, "text", "")[:70], "box": box, "circle": hits})

    out = ROOT / "experiments" / "docling" / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"test1_{model}_{pid}.json").write_text(json.dumps({"circles": circles, "items": items, "seconds": secs}, indent=1))
    print(f"page {pid}, layout {model}: {len(items)} items in {secs:.1f}s; circles at {circles}")
    labels = {}
    for it in items:
        labels[it["label"]] = labels.get(it["label"], 0) + 1
    print("labels:", labels)
    for it in items:
        if it["circle"] or "checkbox" in it["label"] or it["label"] in ("picture", "form", "key_value_region"):
            print(f"  {it['label']:20} circle={it['circle']} {it['box']} {it['text']!r}")


if __name__ == "__main__":
    main()
