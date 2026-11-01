"""Classic OCR engines on the marker crops (no VLM): tesseract 5 (tesserocr wheel), RapidOCR (PP-OCR
models via ONNX, the PaddleOCR lineage), Apple Vision (ocrmac). Crops are upscaled 3x first because
they are 20-200 px tall. Output matches run_crops.py so score_crops.py can score it.
usage: python experiments/marker_crops/run_crops_ocr.py [tesseract,rapidocr,applevision] [--modes marked,clean,inside]
"""
import argparse, json, sys, time
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
IMG = {"marked": "crop_marked", "clean": "crop_clean", "inside": "crop_inside"}
SCALE = 3

def up(path):
    im = Image.open(path).convert("RGB")
    return im.resize((im.width * SCALE, im.height * SCALE), Image.LANCZOS)

def engine(name):
    if name == "tesseract":
        import tesserocr
        api = tesserocr.PyTessBaseAPI(path=str(HERE.parents[1] / ".venv_vlm/tessdata"), lang="eng", psm=tesserocr.PSM.SINGLE_BLOCK)
        def run(im): api.SetImage(im); return api.GetUTF8Text().strip()
        return run
    if name == "rapidocr":
        from rapidocr_onnxruntime import RapidOCR
        import numpy as np
        ocr = RapidOCR()
        def run(im):
            res, _ = ocr(np.array(im))
            return " ".join(r[1] for r in (res or [])).strip()
        return run
    if name == "applevision":
        from ocrmac import ocrmac
        def run(im):
            return " ".join(t for t, conf, box in ocrmac.OCR(im, recognition_level="accurate").recognize()).strip()
        return run
    raise SystemExit(f"unknown engine {name}")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("engines", nargs="?", default="tesseract,rapidocr,applevision")
    ap.add_argument("--modes", default="marked,clean,inside"); a = ap.parse_args()
    pages = sorted(HERE.glob("out/*/markers.json"))
    for name in a.engines.split(","):
        run = engine(name); results = {}
        for mode in a.modes.split(","):
            results[mode] = []
            for mj in pages:
                m = json.loads(mj.read_text()); od = mj.parent
                for mk in m["markers"]:
                    if not mk.get(IMG[mode]): continue
                    t = time.time()
                    try: ans = run(up(od / mk[IMG[mode]]))
                    except Exception as e: ans = f"ERROR: {type(e).__name__}: {e}"
                    results[mode].append(dict(page=m["page"][:2], id=mk["id"], answer=ans, s=round(time.time() - t, 2)))
            print(f"[{name}] {mode}: {len(results[mode])} crops", flush=True)
        out = HERE / "out_vlm" / name; out.mkdir(parents=True, exist_ok=True)
        (out / "results.json").write_text(json.dumps(results, indent=1))
    print("done")

if __name__ == "__main__":
    main()
