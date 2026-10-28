"""Turn OCRia-1's markdown into circle predictions and grade them (found / 38, position ignored).

OCRia's documented formats have no tag for a hand-drawn circle: <u> is underline, <mark> is highlighter,
~~ is strikethrough (report, appendix F). So by default only the explicit "(circled)" note on option lines
counts. Pass formats to also count them as circles, e.g. "mark,strike" or "u,mark,strike".
    .venv_vlm/bin/python experiments/opendocrouter/score.py [plain|layout] [u,mark,strike]
"""
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from formeval import data, grade  # noqa: E402
from formeval.normalize import norm  # noqa: E402

BASE = Path(__file__).parent / "out" / "llamaindex__ocria-1"
SPAN = re.compile(r"<u>(.+?)</u>|<mark>(.+?)</mark>|~~(.+?)~~", re.S)


def clean(s):
    s = re.sub(r"<[^>]+>|~~|\*", "", s)
    return re.sub(r"\s+", " ", s).strip(" ,.;:")


def spans(md):
    out = []
    for m in SPAN.finditer(md):
        kind = ["u", "mark", "strike"][[g is not None for g in m.groups()].index(True)]
        out.append((kind, clean(next(g for g in m.groups() if g))))
    return out


def options(md, schema):
    answers, heading = {q["id"]: None for q in schema["questions"]}, ""
    for line in md.splitlines():
        s = line.strip()
        if not s.startswith("-"):
            heading = s if s.strip("*") else heading
        elif "(circled)" in s:
            q = max(schema["questions"], key=lambda q: SequenceMatcher(None, norm(q["text"]), norm(clean(heading))).ratio())
            opt = clean(s.lstrip("- ").replace("(circled)", ""))
            code = re.search(r":\s*(\d+)$", opt)
            answers[q["id"]] = code.group(1) if code else opt
    return answers


mode = sys.argv[1] if len(sys.argv) > 1 else "plain"
keep = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else set()
found = total = extras_n = 0
for pid in ["01", "02", "03", "04", "05", "06", "20"]:
    md = json.loads((BASE / mode / f"{pid}.json").read_text())["pages"][0]["markdown"]
    truth, schema = data.load_truth(pid), data.load_schema(pid)
    if truth["kind"] == "text":
        sp = spans(md)
        out = {"marked": [{"text": t, "context": ""} for k, t in sp if k in keep]}
    else:
        out = {"answers": options(md, schema)}
    g = grade.grade_page(truth, schema, out, ignore_context=True)
    hits = [r for r in g["results"] if r["expected"] not in (None, [])]
    n = sum(r["correct"] for r in hits)
    found, total, extras_n = found + n, total + len(hits), extras_n + len(g.get("extras", []))
    print(f"page {pid}: {n}/{len(hits)}  missed {[r['expected'] for r in hits if not r['correct']]}")
    if truth["kind"] == "text":
        print("   marked spans:", [f"{k}:{t}" for k, t in sp])
    else:
        print("   answers:", out["answers"])
print(f"FOUND {found}/{total}   extra spans reported: {extras_n}")
