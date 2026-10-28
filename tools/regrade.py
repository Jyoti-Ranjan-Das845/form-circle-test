"""Re-score saved predictions of a run without re-running the pipeline.

Usage:  python tools/regrade.py results/<pipeline>/<run> [--ignore-context]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from formeval import data, grade  # noqa: E402

run_dir = Path(sys.argv[1])
ignore = "--ignore-context" in sys.argv
correct = denom = 0
for f in sorted((run_dir / "predictions").glob("*.json")):
    pid = f.stem
    rep = grade.grade_page(data.load_truth(pid), data.load_schema(pid), json.loads(f.read_text()), ignore)
    correct += rep["correct"]
    denom += rep["items"] + len(rep["extras"])
    print(f"page {pid}  {rep['correct']}/{rep['items']} correct  extras {len(rep['extras'])}  accuracy {rep['accuracy']:.1%}")
print(f"ACCURACY {correct / denom:.1%}  ({correct}/{denom})" + ("  [position of repeated words ignored]" if ignore else ""))
