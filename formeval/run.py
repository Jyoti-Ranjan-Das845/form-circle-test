"""Run a pipeline over the marked pages and score it.

Usage:
    python -m formeval.run --pipeline pipelines/oracle.py
    python -m formeval.run --pipeline pipelines/my_vlm.py:extract --pages 01,02,20 --gray

--pipeline   a .py file or module, optionally with ":function" (default function name: run)
--pages      comma-separated page ids (default: every page that has been marked)
--gray       give the pipeline grey-scale copies, so red ink cannot be used as a shortcut
--ink        black|blue|pencil: repaint the hand marks in that ink on the clean page (main score: black)
--marked-dir folder with the marked pages (default: real_forms_marked)
"""
import argparse
import importlib
import importlib.util
import json
import sys
import tempfile
import time
import traceback
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageChops

from . import contract, data, grade


INKS = {"black": (25, 25, 30), "blue": (30, 45, 150), "pencil": (115, 115, 115)}


def repaint_marks(clean_path, marked_path, ink):
    """Redraw the hand marks (marked page minus clean page) in another ink on the clean page."""
    clean = Image.open(clean_path).convert("RGB")
    marked = Image.open(marked_path).convert("RGB").resize(clean.size)
    mask = ImageChops.difference(clean, marked).convert("L").point(lambda v: 255 if v > 60 else 0)
    out = clean.copy()
    out.paste(Image.new("RGB", clean.size, INKS[ink]), mask=mask)
    return out


def load_pipeline(spec):
    target, _, func = spec.partition(":")
    func = func or "run"
    if target.endswith(".py") or "/" in target:
        path = Path(target).resolve()
        mod_spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(mod_spec)
        sys.path.insert(0, str(path.parent))
        mod_spec.loader.exec_module(module)
        name = path.stem
    else:
        module = importlib.import_module(target)
        name = target.rsplit(".", 1)[-1]
    if not hasattr(module, func):
        sys.exit(f"{target} has no function {func!r}")
    return name if func == "run" else f"{name}.{func}", getattr(module, func)


def build_task(page_id, image_path):
    truth = data.load_truth(page_id)
    schema = data.load_schema(page_id)
    kind = truth["kind"]
    return {"page_id": page_id, "image_path": str(image_path), "kind": kind,
            "instruction": contract.TEXT_INSTRUCTION if kind == "text" else contract.OPTIONS_INSTRUCTION,
            "schema": {"questions": schema["questions"]} if schema else None}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pipeline", required=True)
    ap.add_argument("--pages")
    ap.add_argument("--gray", action="store_true")
    ap.add_argument("--ink", choices=sorted(INKS), help="repaint the hand marks in this ink (overrides --gray)")
    ap.add_argument("--ignore-context", action="store_true",
                    help="count a circled word as found even if it is the wrong occurrence of a repeated word")
    ap.add_argument("--marked-dir", default=str(data.MARKED_DIR))
    ap.add_argument("--out", default=str(data.ROOT / "results"))
    args = ap.parse_args(argv)

    name, fn = load_pipeline(args.pipeline)
    marked_dir = Path(args.marked_dir)
    if args.pages:
        pages = [p.strip().zfill(2) for p in args.pages.split(",")]
    else:
        pages = [p for p in data.all_page_ids() if data.is_marked(p, marked_dir)]
    if not pages:
        sys.exit("no marked pages found — mark some pages in real_forms_marked/ first")

    mode = args.ink or ("gray" if args.gray else "color")
    run_dir = Path(args.out) / name / f"{datetime.now():%Y%m%d-%H%M%S}-{mode}"
    (run_dir / "predictions").mkdir(parents=True)
    tmp = tempfile.TemporaryDirectory()

    reports, total_correct, total_denom = [], 0, 0
    print(f"pipeline: {name}   mode: {mode}   pages: {', '.join(pages)}\n")
    for pid in pages:
        truth = data.load_truth(pid)
        image = marked_dir / truth["image"]
        if args.ink:
            inked = Path(tmp.name) / truth["image"]
            repaint_marks(data.CLEAN_DIR / truth["image"], image, args.ink).save(inked)
            image = inked
        elif args.gray:
            gray = Path(tmp.name) / truth["image"]
            Image.open(image).convert("L").save(gray)
            image = gray
        task = build_task(pid, image)
        started = time.perf_counter()
        error = None
        try:
            output = fn(task)
            contract.validate(task, output)
        except Exception as exc:  # a crashing or malformed page scores 0 instead of stopping the run
            error = f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
            output = {"marked": []} if task["kind"] == "text" else {"answers": {}}
        seconds = time.perf_counter() - started

        (run_dir / "predictions" / f"{pid}.json").write_text(json.dumps(output, indent=2, ensure_ascii=False))
        rep = grade.grade_page(truth, data.load_schema(pid), output, args.ignore_context)
        rep.update({"seconds": round(seconds, 2), "error": error})
        reports.append(rep)
        total_correct += rep["correct"]
        total_denom += rep["items"] + len(rep["extras"])

        misses = [r for r in rep["results"] if not r["correct"]]
        print(f"page {pid} ({rep['kind']:7}) {rep['correct']:>2}/{rep['items']:<2} correct"
              f"  extras {len(rep['extras']):<2} accuracy {rep['accuracy']:6.1%}  {seconds:5.1f}s"
              + (f"  ERROR {error}" if error else ""))
        for r in misses:
            print(f"     ✗ {r['id']:<12} expected {r['expected']!r:<40} got {r['got']!r}")
        for e in rep["extras"]:
            print(f"     + extra: {e!r}")

    accuracy = total_correct / total_denom if total_denom else 0.0
    summary = {"pipeline": name, "mode": mode, "pages": pages, "correct": total_correct,
               "denominator": total_denom, "accuracy": accuracy, "pages_detail": reports}
    (run_dir / "report.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nACCURACY {accuracy:.1%}  ({total_correct} correct / {total_denom} = items + extras)")
    print(f"saved to {run_dir}")
    return summary


if __name__ == "__main__":
    main()
