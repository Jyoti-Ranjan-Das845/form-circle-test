"""Leaderboard and failure analysis over saved colour runs (position of repeated words ignored).

For each run: circles found out of 38, extra items reported, median seconds per page. For the 33 circles on the
text pages it also splits the misses:
    found      reported exactly
    misread    something close was reported (saw the circle, read it wrong or cut it short)
    missed     nothing close was reported
and places every extra item on the clean page with OCR:
    next to a circle   within ~2 lines of a red circle
    elsewhere          printed on the page, away from every circle
    not on page        not printed anywhere (made up or badly garbled)

    .venv_vlm/bin/python tools/failure_analysis.py [--examples]
A run may combine directories: later ones replace pages of earlier ones (re-runs of failed pages).
"""
import json
import statistics
import sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from experiments.marks import circle_boxes  # noqa: E402
from formeval import data, grade  # noqa: E402
from formeval.normalize import norm  # noqa: E402
from pipelines.common import ocr  # noqa: E402

R = "results/"
RUNS = {
    "GPT-6 Luna, medium reasoning (OpenRouter)": [R + "openrouter_luna/openrouter_gemma.run_luna/20261028-125212-color"],
    "Gemma 4 26B-A4B (OpenRouter)": [R + "openrouter_gemma4_26b/openrouter_gemma/20261027-011835-color"],
    "Qwen3-VL-2B bf16, P6 zoomed tiles": [R + "bf16/p6_vlm_tiles/20261026-170226-color"],
    "Qwen3.5-4B 6-bit, thinking on (8k for 01, 04)": [R + "qwen35/direct_vlm.run_qwen35_think/20261027-210532-color",
                                                      R + "qwen35_think8k/direct_vlm.run_qwen35_think/20261027-212051-color"],
    "Qwen3.5-4B 6-bit, thinking off": [R + "qwen35/direct_vlm.run_qwen35/20261027-210324-color"],
    "Gemma 4 E2B 6-bit, image only": [R + "gemma/gemma/20261027-004134-color", R + "gemma_p6/gemma/20261027-004806-color"],
    "Gemma 4 E2B 6-bit, image + OCR": [R + "gemma/gemma.run_ocr/20261027-004358-color"],
    "Qwen3-VL-2B bf16, whole page": [R + "bf16/direct_vlm/20261026-165122-color"],
    "Florence-2-large bf16, P7 detection + OCR": [R + "bf16/p7_vlm_tiles_ocr.run_florence/20261026-174022-color"],
    "Mistral Small 2603 (OpenRouter)": [R + "openrouter_mistral/openrouter_gemma.run_mistral/20261027-014217-color",
                                        R + "openrouter_mistral/openrouter_gemma.run_mistral/20261027-014711-color"],
    "Moondream 3.1 (OpenRouter)": [R + "openrouter_moondream/openrouter_gemma.run_moondream/20261027-012058-color"],
    "Gemma 3 4B (OpenRouter)": [R + "openrouter_gemma3/openrouter_gemma/20261027-011459-color"],
}
TEXT_PAGES = ["01", "02", "03", "04", "05", "06"]


def load(dirs):
    preds, secs = {}, {}
    for d in dirs:
        d = ROOT / d
        for f in (d / "predictions").glob("*.json"):
            preds[f.stem] = json.loads(f.read_text())
        report = d / "report.json"
        if report.exists():
            for p in json.loads(report.read_text())["pages_detail"]:
                if p["page_id"] in preds:
                    secs[p["page_id"]] = p["seconds"]
    return preds, secs


def sim(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0
    if (a in b or b in a) and min(len(a), len(b)) >= 3:
        return 0.9
    return SequenceMatcher(None, a, b).ratio()


_pages = {}


def page_geometry(pid):
    """OCR spans of the clean page, circle boxes from the marked page, and the median word height."""
    if pid not in _pages:
        name = data.load_truth(pid)["image"]
        words = ocr.read(ROOT / "real_forms" / name)["words"]
        boxes = [b for b in circle_boxes(ROOT / "real_forms" / name, ROOT / "real_forms_marked" / name)
                 if b[2] - b[0] > 15 and b[3] - b[1] > 10]
        spans = []
        for i in range(len(words)):
            for n in range(1, 7):
                seg = words[i:i + n]
                if len(seg) < n or seg[-1]["line"] != seg[0]["line"]:
                    break
                spans.append((" ".join(w["text"] for w in seg),
                              [min(w["box"][0] for w in seg), min(w["box"][1] for w in seg),
                               max(w["box"][2] for w in seg), max(w["box"][3] for w in seg)]))
        lh = sorted(w["box"][3] - w["box"][1] for w in words)[len(words) // 2]
        _pages[pid] = (spans, boxes, lh)
    return _pages[pid]


def where(pid, text):
    spans, boxes, lh = page_geometry(pid)
    best = max(spans, key=lambda s: SequenceMatcher(None, norm(s[0]), norm(text)).ratio())
    if SequenceMatcher(None, norm(best[0]), norm(text)).ratio() < 0.8:
        return "not on page"
    x1, y1, x2, y2 = best[1]
    for b in boxes:
        if x1 < b[2] + 2 * lh and x2 > b[0] - 2 * lh and y1 < b[3] + 1.5 * lh and y2 > b[1] - 1.5 * lh:
            return "next to a circle"
    return "elsewhere"


def analyse(dirs):
    preds, secs = load(dirs)
    c = dict(found=0, total=0, extras=0, misread=0, missed=0, text_found=0,
             **{"next to a circle": 0, "elsewhere": 0, "not on page": 0})
    examples = []
    for pid in TEXT_PAGES + ["20"]:
        out = preds.get(pid, {"marked": []} if pid != "20" else {"answers": {}})
        truth = data.load_truth(pid)
        g = grade.grade_page(truth, data.load_schema(pid), out, ignore_context=True)
        hits = [r for r in g["results"] if r["expected"] not in (None, [])]
        c["found"] += sum(r["correct"] for r in hits)
        c["total"] += len(hits)
        c["extras"] += len(g.get("extras", [])) + sum(1 for r in g["results"] if r["expected"] in (None, []) and not r["correct"])
        if truth["kind"] != "text":
            continue
        left = list(g.get("extras", []))
        for r in hits:
            if r["correct"]:
                c["text_found"] += 1
                continue
            near = max(left, key=lambda e: sim(e, r["expected"]), default=None)
            if near is not None and sim(near, r["expected"]) >= 0.6:
                c["misread"] += 1
                left.remove(near)
                examples.append(f'{pid} misread "{r["expected"]}" as "{near}"')
            else:
                c["missed"] += 1
        for e in left:
            w = where(pid, e)
            c[w] += 1
            examples.append(f'{pid} extra ({w}): "{e[:60]}"')
    c["s_page"] = statistics.median(secs.values()) if secs else None
    return c, examples


def main():
    show = "--examples" in sys.argv
    head = ["found/38", "extras", "s/page", "| text:", "found", "misread", "missed", "| extras:", "near circle",
            "elsewhere", "not on page"]
    print(f"{'run':48}" + "".join(f"{h:>12}" for h in head))
    for name, dirs in RUNS.items():
        c, ex = analyse(dirs)
        row = [f"{c['found']}/{c['total']}", c["extras"], f"{c['s_page']:.0f}" if c["s_page"] else "-", "",
               c["text_found"], c["misread"], c["missed"], "", c["next to a circle"], c["elsewhere"], c["not on page"]]
        print(f"{name:48}" + "".join(f"{str(v):>12}" for v in row))
        if show:
            for e in ex:
                print("    " + e)


if __name__ == "__main__":
    main()
