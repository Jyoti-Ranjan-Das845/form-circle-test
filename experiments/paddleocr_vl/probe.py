"""Probe: what does the PaddleOCR-VL-1.6 pipeline return for a hand-marked page?

Two runs on one marked page, no evaluator:
  run 1  full pipeline (layout detection on)       -> regions + text per region
  run 2  layout off, prompt_label="spotting"       -> every text piece + its 4-corner position

Then it lines both up against where the circles really are (marked page minus clean page),
so we can see by hand whether a circle became its own region and whether the circled text was read.

Setup (Apple Silicon): see FINDINGS.md. Needs an MLX-VLM server on port 8111.
Usage:  python experiments/paddleocr_vl/probe.py 04
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments"))
from marks import circle_boxes, overlap  # noqa: E402
SERVER = "http://localhost:8111/"
MODEL = "PaddlePaddle/PaddleOCR-VL-1.6"


def poly_box(poly):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    return [min(xs), min(ys), max(xs), max(ys)]


def to_plain(obj):
    if isinstance(obj, dict):
        return {k: to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_plain(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    return obj


def main():
    from paddleocr import PaddleOCRVL

    pid = sys.argv[1].zfill(2)
    truth = json.loads((ROOT / "data" / "ground_truth" / f"{pid}.json").read_text())
    clean = ROOT / "real_forms" / truth["image"]
    marked = ROOT / "real_forms_marked" / truth["image"]
    out = ROOT / "experiments" / "paddleocr_vl" / "out" / pid
    out.mkdir(parents=True, exist_ok=True)

    pipeline = PaddleOCRVL(pipeline_version="v1.6", vl_rec_backend="mlx-vlm-server",
                           vl_rec_server_url=SERVER, vl_rec_api_model_name=MODEL)

    # ---- run 1: full pipeline
    r1 = list(pipeline.predict(str(marked)))[0]
    r1.save_to_json(save_path=str(out / "run1"))
    r1.save_to_markdown(save_path=str(out / "run1"))
    r1.save_to_img(save_path=str(out / "run1"))
    run1 = to_plain(r1.json)["res"]

    # ---- run 2: layout off, spotting
    r2 = list(pipeline.predict(str(marked), use_layout_detection=False, prompt_label="spotting"))[0]
    r2.save_to_json(save_path=str(out / "run2"))
    r2.save_to_img(save_path=str(out / "run2"))
    run2 = to_plain(r2.json)["res"]

    circles = circle_boxes(clean, marked)
    blocks = run1.get("parsing_res_list", [])
    layout = run1.get("layout_det_res", {}).get("boxes", [])
    spot = run2.get("spotting_res") or {}
    spot_items = list(zip(spot.get("rec_texts", []), spot.get("rec_polys", [])))

    report = []
    for i, cb in enumerate(circles, 1):
        own_region = [{"label": b["label"], "score": round(b["score"], 3), "coordinate": [round(v) for v in b["coordinate"]]}
                      for b in layout if overlap(b["coordinate"], cb) > 0.6]
        in_blocks = [{"label": b["block_label"], "bbox": b["block_bbox"], "content": b["block_content"]}
                     for b in blocks if overlap(cb, b["block_bbox"]) > 0.3]
        spotted = [{"text": t, "box": [round(v) for v in poly_box(p)]}
                   for t, p in spot_items if overlap(poly_box(p), cb) > 0.4]
        report.append({"circle": i, "box": cb, "layout_regions_inside_circle": own_region,
                       "run1_blocks_containing_circle": in_blocks, "run2_spotted_inside_circle": spotted})
    (out / "probe_report.json").write_text(json.dumps(
        {"page": pid, "expected": [it["text"] for it in truth.get("items", [])], "circles": report,
         "layout_labels": sorted({b["label"] for b in layout}), "n_spotted": len(spot_items)},
        indent=2, ensure_ascii=False))

    # picture: circles (red), layout regions (blue), spotting boxes (green)
    img = Image.open(marked).convert("RGB")
    d = ImageDraw.Draw(img)
    for b in layout:
        d.rectangle(b["coordinate"], outline=(40, 90, 255), width=2)
    for _, p in spot_items:
        d.polygon([tuple(v) for v in p], outline=(0, 170, 0))
    for cb in circles:
        d.rectangle(cb, outline=(255, 0, 0), width=2)
    img.save(out / "overlay.png")
    print(f"page {pid}: {len(circles)} circles, {len(layout)} layout regions, {len(spot_items)} spotted pieces -> {out}")


if __name__ == "__main__":
    main()
