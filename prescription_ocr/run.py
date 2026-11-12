#!/usr/bin/env python3
"""Read each prescription photo in images/ with Eka Care's parrotlet-v-2.5-pro and save the JSON it returns.

Two ways to run the same model:

    python run.py --local                 # on this machine's GPU (needs ~11 GB VRAM, transformers>=5.14)
    FEATHERLESS_API_KEY=... python run.py --featherless    # hosted, no GPU needed

    python run.py --local rx8             # just one image
    python run.py --local --images crops/images --out results/local_crops    # the text crops

The prompt is the image plus the exact tag "<prescription>" and nothing else, greedy decoding, up to 2048 new
tokens, as on the model card (https://huggingface.co/ekacare/parrotlet-v-2.5-pro).
Results go to results/<mode>/<image>.json and a one-line summary per image is printed.
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

MODEL = "ekacare/parrotlet-v-2.5-pro"
TAG = "<prescription>"  # must be exact: a typo returns valid-looking but empty JSON
HERE = Path(__file__).resolve().parent
IMAGES = HERE / "images"


def parse(text: str):
    t = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        return None


def local_runner():
    import torch
    from PIL import Image
    from transformers import AutoModelForImageTextToText, AutoProcessor

    print(f"loading {MODEL} …", flush=True)
    model = AutoModelForImageTextToText.from_pretrained(MODEL, dtype=torch.bfloat16, device_map="auto")
    processor = AutoProcessor.from_pretrained(MODEL)

    def run(path: Path) -> dict:
        messages = [{"role": "user", "content": [
            {"type": "image", "image": Image.open(path).convert("RGB")},
            {"type": "text", "text": TAG},
        ]}]
        inputs = processor.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors="pt",
        ).to(model.device)
        n_in = inputs["input_ids"].shape[-1]
        t0 = time.time()
        out = model.generate(**inputs, max_new_tokens=2048, do_sample=False)
        secs = round(time.time() - t0, 1)
        text = processor.decode(out[0][n_in:], skip_special_tokens=True)
        return {"ok": True, "seconds": secs, "usage": {"prompt_tokens": n_in, "completion_tokens": out.shape[-1] - n_in},
                "raw": text, "json": parse(text)}

    return run


def featherless_runner():
    import requests

    key = os.environ.get("FEATHERLESS_API_KEY")
    if not key:
        sys.exit("Set FEATHERLESS_API_KEY first.")

    def run(path: Path) -> dict:
        data_url = "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()
        body = {"model": MODEL, "temperature": 0, "max_tokens": 2048, "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": data_url}},
            {"type": "text", "text": TAG},
        ]}]}
        t0 = time.time()
        r = requests.post("https://api.featherless.ai/v1/chat/completions",
                          headers={"Authorization": f"Bearer {key}"}, json=body, timeout=300)
        secs = round(time.time() - t0, 1)
        if r.status_code != 200:
            return {"ok": False, "status": r.status_code, "error": r.text[:2000], "seconds": secs}
        resp = r.json()
        text = resp["choices"][0]["message"]["content"] or ""
        return {"ok": True, "seconds": secs, "usage": resp.get("usage"), "raw": text, "json": parse(text)}

    return run


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--local", action="store_true", help="run the model on this machine's GPU")
    mode.add_argument("--featherless", action="store_true", help="call the hosted model on Featherless")
    ap.add_argument("--images", default=str(IMAGES), help="folder of .jpeg images (default: images/)")
    ap.add_argument("--out", default=None, help="results folder (default: results/<mode>)")
    ap.add_argument("only", nargs="*", help="image names to run, e.g. rx8 (default: all)")
    args = ap.parse_args()

    name = "local" if args.local else "featherless"
    run = local_runner() if args.local else featherless_runner()
    out_dir = Path(args.out) if args.out else HERE / "results" / name
    out_dir.mkdir(parents=True, exist_ok=True)

    for img in sorted(Path(args.images).glob("*.jpeg")):
        if args.only and img.stem not in args.only:
            continue
        print(f"{img.stem}: reading …", flush=True)
        res = run(img)
        res.update({"image": img.name, "model": MODEL, "tag": TAG, "mode": name})
        (out_dir / f"{img.stem}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
        if not res["ok"]:
            print(f"  failed ({res['status']}): {res['error'][:300]}")
        elif res["json"] is None:
            print(f"  {res['seconds']}s · output is not valid JSON (see raw in the file)")
        else:
            print(f"  {res['seconds']}s · {res['usage']} · saved {out_dir.name}/{img.stem}.json")
    print(f"\nResults in {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
