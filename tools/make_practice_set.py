"""Practice set: hand-drawn-style circles around random words on spare RVL-CDIP pages (never the 20 test pages).

Used only to tune rule-based parts (P1's mark finder). Nothing is trained.
Usage:  .venv_vlm/bin/python tools/make_practice_set.py --n 24
"""
import argparse
import json
import random
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipelines.common import ocr  # noqa: E402

INKS = [(25, 25, 30), (150, 45, 30), (115, 115, 115), (30, 30, 200)]  # BGR: black, blue, pencil, red


def wobbly_loop(cx, cy, rx, ry, rng):
    start = rng.uniform(0, 2 * np.pi)
    sweep = rng.uniform(1.75, 2.15) * np.pi          # some open, some overlapping
    t = np.linspace(start, start + sweep, 160)
    wob = 1 + 0.06 * np.sin(t * rng.uniform(2, 4) + rng.uniform(0, 6)) + rng.normal(0, 0.01, t.size)
    rot = rng.uniform(-0.12, 0.12)
    x, y = rx * wob * np.cos(t), ry * wob * np.sin(t)
    xr, yr = x * np.cos(rot) - y * np.sin(rot), x * np.sin(rot) + y * np.cos(rot)
    return np.stack([cx + xr, cy + yr], 1).astype(np.int32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--seed", type=int, default=3)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    random.seed(args.seed)
    test_sources = {  # the 20 test pages' source scans: never reused
        "sci_report_train_0299", "sci_report_train_0297", "sci_pub_train_0321", "sci_report_train_0250",
        "memo_train_0792", "letter_train_0011", "questionnaire_train_0655", "letter_train_0006", "memo_train_0757",
        "memo_validation_0392", "questionnaire_train_0662", "questionnaire_train_0692", "questionnaire_validation_0341",
        "questionnaire_train_0695", "questionnaire_test_0326", "questionnaire_validation_0338",
        "questionnaire_train_0650", "questionnaire_test_0347", "questionnaire_validation_0332",
        "questionnaire_train_0686"}
    pool = sorted(p for p in (ROOT / "downloads" / "rvl_candidates").glob("*.tif")
                  if p.stem.split("_")[0] in {"letter", "memo", "sci", "questionnaire", "form"}
                  and p.stem not in test_sources)
    random.shuffle(pool)
    out = ROOT / "practice"
    (out / "pages").mkdir(parents=True, exist_ok=True)
    truth = {}
    for src in pool:
        if len(truth) >= args.n:
            break
        img = cv2.imread(str(src))
        if img is None:
            continue
        page = ocr.read(img)
        words = [w for w in page["words"] if len(w["text"]) >= 3 and w["text"].isalnum()]
        if len(words) < 40:
            continue
        chosen, boxes = [], []
        for w in random.sample(words, len(words)):
            x1, y1, x2, y2 = w["box"]
            if any(not (x2 + 15 < b[0] or b[2] + 15 < x1 or y2 + 15 < b[1] or b[3] + 15 < y1) for b in boxes):
                continue
            chosen.append(w)
            boxes.append(w["box"])
            if len(chosen) == 4:
                break
        ink = INKS[int(rng.integers(len(INKS)))]
        for w in chosen:
            x1, y1, x2, y2 = w["box"]
            pad_x, pad_y = rng.uniform(1, 9), rng.uniform(-1, 6)
            loop = wobbly_loop((x1 + x2) / 2, (y1 + y2) / 2, (x2 - x1) / 2 + pad_x, (y2 - y1) / 2 + pad_y, rng)
            cv2.polylines(img, [loop], False, ink, int(rng.integers(2, 4)), lineType=cv2.LINE_AA)
        name = f"{len(truth):02d}_{src.stem}.png"
        cv2.imwrite(str(out / "pages" / name), img)
        truth[name] = [{"text": w["text"], "box": w["box"]} for w in chosen]
    (out / "truth.json").write_text(json.dumps(truth, indent=1))
    print(f"{len(truth)} practice pages -> {out}")


if __name__ == "__main__":
    main()
