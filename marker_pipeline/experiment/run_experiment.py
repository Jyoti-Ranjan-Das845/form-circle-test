"""Run the pipeline on the dataset and score it.

    python experiment/run_experiment.py --readers paddleocr-vl,rapidocr --modes marked,inside

Detection runs once (reused when outputs exist, unless --redetect). Readers run one after another and each is
closed before the next loads, so only one model is in memory at a time. Results:
    experiment/outputs/                        detection output and raw answers (regenerable, not committed)
    experiment/outputs/scores.json             all scores
    experiment/outputs/scores.md               the summary table
"""
import argparse
import json
import logging
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # run from anywhere without installing

from markpipe import DetectorConfig, create_reader, detect_pages, find_pairs, read_crops  # noqa: E402
from markpipe.pipeline import MODES  # noqa: E402
from markpipe.readers import ReaderError  # noqa: E402
from score import load_key, score_detection, score_rows  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=str(HERE / "dataset" / "ready_to_use"))
    ap.add_argument("--out", default=str(HERE / "outputs"))
    ap.add_argument("--readers", default="", help="comma list of reader specs; empty = detection only")
    ap.add_argument("--modes", default="marked,inside", help=f"comma list of {', '.join(MODES)}")
    ap.add_argument("--redetect", action="store_true", help="run detection again even if outputs exist")
    ap.add_argument("--base-url", help="for openai:<model> readers")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO if a.verbose else logging.WARNING, format="%(levelname)s %(message)s")

    out, key = Path(a.out), load_key()
    summary_file = out / "summary.json"
    if a.redetect or not summary_file.exists():
        detect_pages(find_pairs(a.data), out, DetectorConfig())
    summary = json.loads(summary_file.read_text())
    det = score_detection(summary, key)
    print("Detection:", ", ".join(f"{p} {v['marks']}/{v['items']}" for p, v in det.items()),
          f"| total {sum(v['marks'] for v in det.values())}/{sum(v['items'] for v in det.values())}")

    scores, table = {"detection": det, "readers": {}}, []
    for spec in [s.strip() for s in a.readers.split(",") if s.strip()]:
        try:
            with create_reader(spec, **({"base_url": a.base_url} if spec.startswith("openai:") else {})) as reader:
                results = read_crops(out, reader, [m.strip() for m in a.modes.split(",")])
        except ReaderError as e:
            print(f"{spec}: skipped ({e})")
            continue
        scores["readers"][spec] = {}
        for mode, rows in results.items():
            s = score_rows(rows, key)
            scores["readers"][spec][mode] = s
            t = s["total"]
            table.append(f"| {spec} | {mode} | {t['hit']}/{t['items']} | {t['exact']}/{t['items']} | "
                         f"{t['extras']} | {t['errors']} | {t['s_per_crop']} |")
            for page, p in s["pages"].items():
                if p["missed"] or p["extras"]:
                    print(f"  {spec} [{mode}] {page}: missed {p['missed']} extras {p['extras']}")

    if table:
        md = "\n".join(["| reader | crops | found | exact | extras | errors | s/crop |",
                        "|---|---|---|---|---|---|---|", *table])
        print("\n" + md)
        (out / "scores.md").write_text(md + "\n")
    (out / "scores.json").write_text(json.dumps(scores, indent=1))


if __name__ == "__main__":
    main()
