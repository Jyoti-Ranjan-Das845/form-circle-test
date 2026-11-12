"""Same job as prescription_ocr/run.py, on Apple Silicon via mlx-vlm with the locally converted 8-bit
Parrotlet-v 2.5 Pro (~/models/parrotlet-v-2.5-pro-8bit). Image + exact tag, greedy, 2048 new tokens.
usage: python prescription_ocr/run_mlx.py prescription_ocr/images prescription_ocr/results/mlx [--tag '<prescription>'] [names...]
"""
import argparse, json, re, sys, time
from pathlib import Path

def parse(text):
    t = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try: return json.loads(t)
    except json.JSONDecodeError: return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("image_dir"); ap.add_argument("out_dir")
    ap.add_argument("--tag", default="<prescription>"); ap.add_argument("--model", default=str(Path.home() / "models/parrotlet-v-2.5-pro-8bit"))
    ap.add_argument("--rep-penalty", type=float, default=None, help="repetition penalty, e.g. 1.1, for pages that loop")
    ap.add_argument("--suffix", default="", help="suffix for the output file name")
    ap.add_argument("only", nargs="*"); a = ap.parse_args()
    import mlx.core as mx
    from mlx_vlm import load, generate
    from mlx_vlm.prompt_utils import apply_chat_template
    model, proc = load(a.model)
    chat = apply_chat_template(proc, model.config, a.tag, num_images=1, enable_thinking=False)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    for img in sorted(Path(a.image_dir).glob("*.jp*g")):
        if a.only and img.stem not in a.only: continue
        t0 = time.time()
        gen_kw = {"repetition_penalty": a.rep_penalty} if a.rep_penalty else {}
        r = generate(model, proc, chat, image=[str(img)], max_tokens=2048, temperature=0.0, verbose=False, **gen_kw)
        secs = round(time.time() - t0, 1)
        text = re.split(r"<channel\|>|</think>", r.text)[-1].replace("<turn|>", "")
        res = {"ok": True, "seconds": secs, "usage": {"prompt_tokens": getattr(r, "prompt_tokens", None), "completion_tokens": getattr(r, "generation_tokens", None)},
               "raw": text, "json": parse(text), "image": img.name, "model": "ekacare/parrotlet-v-2.5-pro (mlx 8-bit local)", "tag": a.tag, "mode": "mlx", "repetition_penalty": a.rep_penalty,
               "peak_memory_gb": round(mx.get_peak_memory() / 1e9, 1)}
        (out / f"{img.stem}{a.suffix}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
        print(f"{img.stem}: {secs}s, {len(text)} chars, json={'ok' if res['json'] is not None else 'INVALID'}, peak {res['peak_memory_gb']} GB", flush=True)

if __name__ == "__main__":
    main()
