"""Run Parrotlet-v 2.5 Pro (local MLX 8-bit) on cropped prescription pieces that have ground-truth text,
and score the transcription against the ground truth.

Ground truth is looked up per image, in this order:
  <stem>.txt next to the image          one file per crop
  gt.json in the image folder            {"<stem or file name>": "text", ...}
  gt.csv in the image folder             columns: image,text   (header required)

Two passes per crop:
  free   prompt "Transcribe all the text in this image exactly as written."  -> scored with CER / WER / word F1
  tag    prompt "<prescription>" (the model's own schema)                     -> scored by how many GT words appear in the JSON

usage: python prescription_ocr/run_gt_crops.py prescription_ocr/crops/images prescription_ocr/results/mlx_crops_free [--model PATH] [--rep-penalty 1.1] [names...]
"""
import argparse, csv, json, re, sys, time
from collections import Counter
from pathlib import Path

FREE_PROMPT = "Transcribe all the text in this image exactly as written. Output only the text."
TAG = "<prescription>"
EXT = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp")

def norm(s):
    s = s.lower().replace("’", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"<[^>]+>|[*_#`|]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def scores(ref, hyp):
    ref, hyp = norm(ref), norm(hyp)
    cer = lev(ref, hyp) / max(1, len(ref)); wer = lev(ref.split(), hyp.split()) / max(1, len(ref.split()))
    rc, hc = Counter(ref.split()), Counter(hyp.split())
    common = sum((rc & hc).values()); prec = common / max(1, sum(hc.values())); rec = common / max(1, sum(rc.values()))
    f1 = 2 * prec * rec / max(1e-9, prec + rec)
    return dict(cer=round(cer, 3), wer=round(wer, 3), word_f1=round(f1, 3), word_recall=round(rec, 3))

def load_gt(folder):
    gt = {}
    for g in (folder / "ground_truth.json", folder.parent / "ground_truth.json"):   # prescription_ocr/crops format
        if g.exists():
            for k, v in json.loads(g.read_text()).items(): gt[Path(k).stem] = v["text"] if isinstance(v, dict) else v
    for j in (folder / "gt.json",):
        if j.exists():
            for k, v in json.loads(j.read_text()).items(): gt[Path(k).stem] = v
    c = folder / "gt.csv"
    if c.exists():
        with open(c, newline="") as f:
            for row in csv.DictReader(f): gt[Path(row["image"]).stem] = row["text"]
    for t in folder.glob("*.txt"):
        if t.stem != "gt": gt[t.stem] = t.read_text()
    return gt

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("image_dir"); ap.add_argument("out_dir")
    ap.add_argument("--model", default=str(Path.home() / "models/parrotlet-v-2.5-pro-8bit"))
    ap.add_argument("--rep-penalty", type=float, default=None); ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("only", nargs="*"); a = ap.parse_args()
    folder = Path(a.image_dir); gt = load_gt(folder)
    images = sorted(p for p in folder.iterdir() if p.suffix.lower() in EXT)
    if a.only: images = [p for p in images if p.stem in a.only]
    if not images: sys.exit(f"no images in {folder}")
    missing = [p.name for p in images if p.stem not in gt]
    if missing: print(f"WARNING no ground truth for: {missing}", flush=True)
    import mlx.core as mx
    from mlx_vlm import load, generate
    from mlx_vlm.prompt_utils import apply_chat_template
    model, proc = load(a.model)
    chats = {k: apply_chat_template(proc, model.config, p, num_images=1, enable_thinking=False) for k, p in (("free", FREE_PROMPT), ("tag", TAG))}
    gen_kw = {"repetition_penalty": a.rep_penalty} if a.rep_penalty else {}
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True); rows = []
    for img in images:
        rec = {"image": img.name, "gt": gt.get(img.stem)}
        for k, chat in chats.items():
            t0 = time.time()
            r = generate(model, proc, chat, image=[str(img)], max_tokens=a.max_tokens, temperature=0.0, verbose=False, **gen_kw)
            text = re.split(r"<channel\|>|</think>", r.text)[-1].replace("<turn|>", "").strip()
            rec[k] = {"seconds": round(time.time() - t0, 1), "raw": text}
        if rec["gt"]:
            rec["free"]["scores"] = scores(rec["gt"], rec["free"]["raw"])
            words = norm(rec["gt"]).split(); jtxt = norm(rec["tag"]["raw"])
            rec["tag"]["gt_words_found"] = f"{sum(w in jtxt for w in words)}/{len(words)}"
        (out / f"{img.stem}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False)); rows.append(rec)
        s = rec["free"].get("scores", {})
        print(f"{img.stem}: free CER {s.get('cer', '-')} wordF1 {s.get('word_f1', '-')} | tag words {rec['tag'].get('gt_words_found', '-')} | {rec['free']['seconds']}s+{rec['tag']['seconds']}s", flush=True)
    scored = [r for r in rows if r.get("gt")]
    if scored:
        mean = lambda k: sum(r["free"]["scores"][k] for r in scored) / len(scored)
        summary = {"crops": len(rows), "scored": len(scored), "free_mean_cer": round(mean("cer"), 3), "free_mean_wer": round(mean("wer"), 3),
                   "free_mean_word_f1": round(mean("word_f1"), 3), "peak_memory_gb": round(mx.get_peak_memory() / 1e9, 1), "model": a.model, "rep_penalty": a.rep_penalty}
        (out / "summary.json").write_text(json.dumps(summary, indent=2)); print(summary)
        with open(out / "RESULTS.md", "w") as f:
            f.write("| crop | GT | free transcription | CER | word F1 | GT words in tag JSON |\n|---|---|---|---|---|---|\n")
            for r in scored:
                f.write(f"| {r['image']} | {norm(r['gt'])[:60]} | {norm(r['free']['raw'])[:60]} | {r['free']['scores']['cer']:.1%} | {r['free']['scores']['word_f1']:.1%} | {r['tag']['gt_words_found']} |\n")
            f.write(f"\nmean CER {summary['free_mean_cer']:.1%}, mean word F1 {summary['free_mean_word_f1']:.1%}, {len(scored)} crops\n")

if __name__ == "__main__":
    main()
