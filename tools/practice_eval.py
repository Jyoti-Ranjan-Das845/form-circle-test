"""Score a mark finder on the practice set (synthetic circles on spare pages). Never touches the test pages.

Usage:  .venv_vlm/bin/python tools/practice_eval.py
Reports recall (circled words found) and false finds (groups that match no circled word).
"""
import json
import sys
import time
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from formeval.normalize import same_text  # noqa: E402
from pipelines.common import marks_cv, ocr  # noqa: E402


def find_groups(path):
    first = ocr.read(path)
    cands = marks_cv.candidates(path, first)
    shape = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE).shape
    page = ocr.best_reading(ocr.read_without(path, marks_cv.stroke_mask(shape, cands)), first) if cands else first
    return [" ".join(page["words"][i]["text"] for i in g) for g in marks_cv.circled_groups(page, cands)]


def main():
    truth = json.loads((ROOT / "practice" / "truth.json").read_text())
    hit = total = false = 0
    t = time.perf_counter()
    for name, items in truth.items():
        found = find_groups(ROOT / "practice" / "pages" / name)
        used = set()
        for it in items:
            total += 1
            k = next((k for k, f in enumerate(found) if k not in used and (same_text(f, it["text"]) or it["text"].lower() in f.lower())), None)
            if k is not None:
                used.add(k)
                hit += 1
        false += len(found) - len(used)
        if "-v" in sys.argv:
            print(name, "expected", [i["text"] for i in items], "found", found)
    print(f"recall {hit}/{total} = {hit / total:.0%}   false finds {false}   {(time.perf_counter() - t) / len(truth):.1f}s/page")


if __name__ == "__main__":
    main()
