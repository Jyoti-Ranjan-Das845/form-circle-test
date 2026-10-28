"""Probe: can Qwen3-VL-2B (4-bit, local MLX) tell what is circled on a marked page?

Two prompts, each on the colour page and on a grey copy (so red ink can't be the shortcut):
  direct    "list the printed text that is circled"           -> text
  grounded  "give a box for every hand-drawn circle"          -> boxes, checked against the real circles

No evaluator; prints what came back, timings, and a per-circle check.
Usage:  .venv_vlm/bin/python experiments/qwen3vl/probe.py 04
"""
import json
import re
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT))
from marks import circle_boxes, iou, overlap  # noqa: E402
from formeval.normalize import same_text  # noqa: E402

MODEL = "mlx-community/Qwen3-VL-2B-Instruct-4bit"

PROMPTS = {
    "direct": (
        "This is a scanned document page. Some printed words or phrases have been circled by hand with a pen. "
        "List every piece of printed text that is circled, exactly as printed, one per line. "
        "Output only the circled text, nothing else."
    ),
    "grounded": (
        "This is a scanned document page with some hand-drawn pen circles around printed text. "
        "Locate every hand-drawn circle. Output a JSON list like "
        '[{"bbox_2d": [x1, y1, x2, y2], "label": "the printed text inside the circle"}]. Output only the JSON.'
    ),
}
MAX_TOKENS = {"direct": 200, "grounded": 500}


def parse_boxes(text, w, h):
    """Qwen3-VL gives boxes on a 0-1000 scale relative to the image; convert to pixels."""
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return []
    try:
        items = json.loads(m.group(0))
    except json.JSONDecodeError:
        items = [{"bbox_2d": [float(v) for v in b], "label": ""}
                 for b in re.findall(r"\[\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\]", text)]
    out = []
    for it in items if isinstance(items, list) else []:
        b = it.get("bbox_2d") if isinstance(it, dict) else None
        if isinstance(b, list) and len(b) == 4:
            x1, y1, x2, y2 = (float(v) for v in b)
            out.append({"box": [round(x1 / 1000 * w), round(y1 / 1000 * h), round(x2 / 1000 * w), round(y2 / 1000 * h)],
                        "label": str(it.get("label", ""))})
    return out


def main():
    from mlx_vlm import generate, load
    from mlx_vlm.prompt_utils import apply_chat_template

    pid = sys.argv[1].zfill(2)
    truth = json.loads((ROOT / "data" / "ground_truth" / f"{pid}.json").read_text())
    clean = ROOT / "real_forms" / truth["image"]
    marked = ROOT / "real_forms_marked" / truth["image"]
    expected = [it["text"] for it in truth.get("items", [])]
    circles = circle_boxes(clean, marked)
    out = ROOT / "experiments" / "qwen3vl" / "out" / pid
    out.mkdir(parents=True, exist_ok=True)

    tmp = tempfile.mkdtemp()
    gray = Path(tmp) / "gray.png"
    Image.open(marked).convert("L").convert("RGB").save(gray)
    images = {"color": str(marked), "gray": str(gray)}
    w, h = Image.open(marked).size

    t = time.perf_counter()
    model, processor = load(MODEL)
    load_s = time.perf_counter() - t
    config = model.config
    # warm-up so the first timed call doesn't include one-off compilation
    generate(model, processor, apply_chat_template(processor, config, "Describe this image in one word.", num_images=1),
             image=[images["color"]], max_tokens=5, temperature=0.0, verbose=False)

    results = {"page": pid, "model": MODEL, "load_seconds": round(load_s, 1), "expected": expected,
               "true_circles": circles, "runs": {}}
    for mode, img in images.items():
        for name, text in PROMPTS.items():
            prompt = apply_chat_template(processor, config, text, num_images=1)
            t = time.perf_counter()
            res = generate(model, processor, prompt, image=[img], max_tokens=MAX_TOKENS[name], temperature=0.0, verbose=False)
            secs = time.perf_counter() - t
            answer = res.text if hasattr(res, "text") else str(res)
            run = {"seconds": round(secs, 2), "raw": answer,
                   "prompt_tokens": getattr(res, "prompt_tokens", None), "output_tokens": getattr(res, "generation_tokens", None)}
            if name == "direct":
                lines = [l.strip(" -*•\t") for l in answer.splitlines() if l.strip(" -*•\t")]
                run["found"] = [e for e in expected if any(same_text(e, l) or e.lower() in l.lower() for l in lines)]
                run["extras"] = [l for l in lines if not any(same_text(e, l) or e.lower() in l.lower() for e in expected)]
            else:
                boxes = parse_boxes(answer, w, h)
                matched = []
                for c in circles:
                    best = max(boxes, key=lambda b: iou(b["box"], c), default=None)
                    hit = best is not None and (iou(best["box"], c) > 0.3 or overlap(best["box"], c) > 0.6)
                    matched.append({"circle": c, "hit": hit, "box": best["box"] if hit else None,
                                    "label": best["label"] if hit else None})
                run.update({"boxes": boxes, "circles_hit": sum(m["hit"] for m in matched), "per_circle": matched})
                img_draw = Image.open(img).convert("RGB")
                d = ImageDraw.Draw(img_draw)
                for c in circles:
                    d.rectangle(c, outline=(255, 0, 0), width=2)
                for b in boxes:
                    d.rectangle(b["box"], outline=(0, 160, 0), width=2)
                img_draw.save(out / f"grounded_{mode}.png")
            results["runs"][f"{name}_{mode}"] = run
            print(f"{name:8} {mode:5} {secs:6.1f}s  " + (f"found {len(run['found'])}/{len(expected)}  extras {len(run['extras'])}"
                  if name == "direct" else f"boxes {len(run['boxes'])}  circles hit {run['circles_hit']}/{len(circles)}"))
    (out / "probe_report.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"model load {load_s:.1f}s -> {out}")


if __name__ == "__main__":
    main()
