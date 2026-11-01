"""Ask a VLM what is inside each detected marker crop.
modes:  marked = marked crop alone
        both   = marked crop + clean crop together
        inside = clean crop with outside-of-circle whitened (no ink at all)
usage: python experiments/marker_crops/run_crops.py qwen35_9b [--modes marked,both]
"""
import argparse, json, re, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
HERE = Path(__file__).resolve().parent
MODELS = {  # key: (repo, thinking flag or None, fixed prompt for OCR-only models or None)
    "qwen35_9b": ("mlx-community/Qwen3.5-9B-4bit", False, None),
    "qwen35_4b": ("mlx-community/Qwen3.5-4B-8bit", False, None),
    "paddle_vl": ("mlx-community/PaddleOCR-VL-1.6-4bit", None, "OCR:"),
    "glm_ocr":   ("mlx-community/GLM-OCR-bf16", None, "Text Recognition:"),
}
PROMPTS = {
    "marked": "What text is inside the red circle? Reply with only that text, exactly as printed.",
    "both":   "Image 1 is a crop of a page with a red pen circle. Image 2 is the same crop without the circle. "
              "What text is inside the red circle? Reply with only that text, exactly as printed.",
    "inside": "What text is in this image? Reply with only the text, exactly as printed.",
    "clean":  "What text is in this image? Reply with only the text, exactly as printed.",
}
IMG = {"marked": ("crop_marked",), "both": ("crop_marked", "crop_clean"), "inside": ("crop_inside",), "clean": ("crop_clean",)}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("model", choices=MODELS)
    ap.add_argument("--modes", default="marked,both"); a = ap.parse_args()
    from mlx_vlm import load, generate
    from mlx_vlm.prompt_utils import apply_chat_template
    repo, think, fixed = MODELS[a.model]
    t0 = time.time(); model, proc = load(repo); print(f"loaded {repo} in {time.time()-t0:.0f}s", flush=True)
    out = HERE / "out_vlm" / a.model; out.mkdir(parents=True, exist_ok=True)
    pages = sorted(HERE.glob("out/*/markers.json"))
    results = {}
    for mode in a.modes.split(","):
        prompt = fixed or PROMPTS[mode]
        kw = {} if think is None else {"enable_thinking": think}
        try: chat = apply_chat_template(proc, model.config, prompt, num_images=len(IMG[mode]), **kw)
        except Exception as e: print(f"no chat template ({type(e).__name__}); raw prompt", flush=True); chat = prompt
        results[mode] = []
        for mj in pages:
            m = json.loads(mj.read_text()); od = mj.parent
            for mk in m["markers"]:
                paths = [str(od / mk[k]) for k in IMG[mode] if mk.get(k)]
                if len(paths) != len(IMG[mode]): continue
                t = time.time()
                try:
                    r = generate(model, proc, chat, image=paths, max_tokens=60, temperature=0.0, verbose=False)
                    text = r.text if hasattr(r, "text") else str(r)
                except Exception as e:
                    text = f"ERROR: {type(e).__name__}: {e}"
                ans = re.split(r"<channel\|>|</think>", text)[-1].replace("<turn|>", "").strip()
                results[mode].append(dict(page=m["page"][:2], id=mk["id"], answer=ans, s=round(time.time()-t, 1)))
                print(f"[{mode}] {m['page'][:2]} #{mk['id']} ({time.time()-t:.1f}s): {ans[:80]!r}", flush=True)
        (out / "results.json").write_text(json.dumps(results, indent=1))
    print("done", flush=True)

if __name__ == "__main__":
    main()
