"""Render every template to a 300-dpi PNG and a ground-truth JSON of option boxes.

Usage:  .venv/bin/python src/render_forms.py [--out build]
"""
import argparse
import csv
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from templates import TEMPLATES, Form

SCALE = 300 / 96  # CSS px -> 300 dpi pixels

COLLECT_JS = """() => {
  const r = e => { const b = e.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; };
  const opts = [...document.querySelectorAll('.opt[data-qid]')].map(e => ({qid: e.dataset.qid, label: e.dataset.label, box: r(e)}));
  const regions = {};
  for (const e of document.querySelectorAll('[data-qid]:not(.opt)')) {
    const [a, b, c, d] = r(e), q = e.dataset.qid, p = regions[q];
    regions[q] = p ? [Math.min(p[0], a), Math.min(p[1], b), Math.max(p[2], c), Math.max(p[3], d)] : [a, b, c, d];
  }
  return {opts, regions};
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="build")
    args = ap.parse_args()
    out = Path(args.out)
    for d in ("clean", "ground_truth"):
        (out / d).mkdir(parents=True, exist_ok=True)

    answer_rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 816, "height": 1056}, device_scale_factor=SCALE)
        for i, tpl in enumerate(TEMPLATES, 1):
            form_id = f"{i:02d}_{tpl.__name__}"
            form = Form(form_id, tpl.__name__, seed=i)
            page.set_content(tpl(form), wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(150)

            png = out / "clean" / f"{form_id}.png"
            page.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": 816, "height": 1056})

            geo = page.evaluate(COLLECT_JS)
            sc = lambda b: [round(v * SCALE) for v in b]
            questions = []
            for q in form.questions:
                boxes = {o["label"]: sc(o["box"]) for o in geo["opts"] if o["qid"] == q["id"]}
                missing = [o for o in q["options"] if o not in boxes]
                assert not missing, f"{form_id} {q['id']} missing boxes for {missing}"
                questions.append({**q, "region": sc(geo["regions"].get(q["id"], [0, 0, 0, 0])),
                                  "options": [{"label": o, "box": boxes[o]} for o in q["options"]],
                                  "answer": None})
                answer_rows.append({"form_id": form_id, "question_id": q["id"], "question": q["text"],
                                    "select": q["select"], "options": " | ".join(q["options"]), "your_circled_answer": ""})
            gt = {"form_id": form_id, "image": f"clean/{form_id}.png", "width": 2550, "height": 3300,
                  "box_format": "x1,y1,x2,y2 in image pixels", "questions": questions}
            (out / "ground_truth" / f"{form_id}.json").write_text(json.dumps(gt, indent=1))
            print(f"{form_id}: {len(questions)} questions")
        browser.close()

    with open(out / "answer_sheet.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(answer_rows[0]))
        w.writeheader()
        w.writerows(answer_rows)
    print(f"total questions: {len(answer_rows)}")


if __name__ == "__main__":
    main()
