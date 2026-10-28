"""Re-parse saved raw replies of a direct_vlm run with the current parser and score found / circles.

    .venv_vlm/bin/python tools/reparse.py results/qwen35/direct_vlm.run_qwen35/<run>
Rewrites each prediction's "marked" list from its "raw" reply (text pages); options pages are re-scored as saved.
For thinking runs (directory name contains "think") only the text after </think> is the answer; a reply that
never closes its reasoning has no answer.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from formeval import data, grade  # noqa: E402
from pipelines import direct_vlm  # noqa: E402

THINKING = "think" in sys.argv[1]


def answer(raw):
    if not THINKING:
        return raw
    return raw.split("</think>", 1)[1] if "</think>" in raw else ""

found = total = 0
for f in sorted(Path(sys.argv[1], "predictions").glob("*.json")):
    pid, out = f.stem, json.loads(f.read_text())
    truth = data.load_truth(pid)
    if truth["kind"] == "text" and "raw" in out:
        out["marked"] = direct_vlm.words(answer(out["raw"]))
        f.write_text(json.dumps(out, indent=2))
    g = grade.grade_page(truth, data.load_schema(pid), out, ignore_context=True)
    hits = [r for r in g["results"] if r["expected"] not in (None, [])]
    n = sum(r["correct"] for r in hits)
    found, total = found + n, total + len(hits)
    shown = [m["text"] for m in out["marked"]][:12] if "marked" in out else out["answers"]
    print(f"{pid}: {n}/{len(hits)}  extras {len(g.get('extras', []))}  {shown}")
print(f"FOUND {found}/{total}")
