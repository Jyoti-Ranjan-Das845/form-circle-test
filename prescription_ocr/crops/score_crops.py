#!/usr/bin/env python3
"""Check whether a model read the text in each crop.

    python prescription_ocr/crops/score_crops.py prescription_ocr/results/mlx_crops

The results folder holds one <crop>.json per crop, as written by run.py or run_mlx.py (the "raw" field is the
model's output). For each crop, every word and number of the ground truth is looked for in that output, ignoring
case, spaces and punctuation around it. A crop counts as fully read when every piece is found.
Writes CROP_SCORES.md into the results folder. Standard library only.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GT = json.loads((HERE / "ground_truth.json").read_text())


def pieces(text: str):
    """Words and numbers of the ground truth: 'Bp - 110/82 mm' -> ['bp', '110/82', 'mm']."""
    out = []
    for tok in re.split(r"[\s,()]+", text.lower()):
        tok = tok.strip(".:-%+")
        if tok and tok not in ("-",):
            out.append(tok)
    return out


def squash(s: str) -> str:
    return re.sub(r"[^a-z0-9./]", "", s.lower())


def main():
    res = Path(sys.argv[1])
    rows, n_all, n_found, full = [], 0, 0, 0
    for crop, g in GT.items():
        f = res / f"{crop}.json"
        raw = json.loads(f.read_text()).get("raw", "") if f.exists() else None
        want = pieces(g["text"])
        if raw is None:
            rows.append((crop, g["text"], "no result file", 0, len(want), ""))
            n_all += len(want)
            continue
        hay = squash(raw)
        # "110/82" also counts when the model split it into 110 and 82 (JSON output does this)
        found = lambda w: squash(w) in hay or ("/" in w and all(squash(x) in hay for x in w.split("/") if x))
        got = [w for w in want if squash(w) and found(w)]
        miss = [w for w in want if w not in got]
        n_all += len(want)
        n_found += len(got)
        full += not miss
        rows.append((crop, g["text"], raw.strip().replace("\n", " ")[:160], len(got), len(want), ", ".join(miss)))

    L = ["# Crop text check", "",
         f"Results: `{res.name}/` · ground truth: `crops/ground_truth.json`", "",
         f"**Crops fully read: {full}/{len(GT)}** · words and numbers found: {n_found}/{n_all} "
         f"({round(100 * n_found / max(n_all, 1))}%)", "",
         "| crop | written on the page | found | missing | model output (start) |", "|---|---|---|---|---|"]
    for crop, text, raw, a, b, miss in rows:
        L.append(f"| {crop} | {text.replace(chr(10), ' / ')} | {a}/{b} | {miss} | `{raw.replace('|', '¦')}` |")
    (res / "CROP_SCORES.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
