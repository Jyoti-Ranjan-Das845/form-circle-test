"""Command line.

    python -m markpipe detect  --data DIR --out DIR [--pages img_01,img_20] [detector options]
    python -m markpipe read    --out DIR --reader SPEC [reader options]
    python -m markpipe run     --data DIR --out DIR --reader SPEC [...]      (detect, then read)
    python -m markpipe readers                                              (list reader presets)
"""
import argparse
import logging
import sys

from .config import DetectorConfig
from .dataset import find_pairs
from .pipeline import detect_pages, read_crops
from .readers import PRESETS, ReaderError, create_reader


def _csv(text):
    return [t.strip() for t in text.split(",") if t.strip()] if text else None


def _add_detect(p):
    p.add_argument("--data", required=True, help="folder with <page>_marked / <page>_unmarked images")
    d = DetectorConfig()
    g = p.add_argument_group("detector")
    g.add_argument("--diff-thresh", type=int, default=d.diff_thresh, help="min channel change counted as ink (0-255)")
    g.add_argument("--gap", type=int, default=d.gap, help="px; stroke breaks up to 2*gap are bridged")
    g.add_argument("--min-area", type=int, default=d.min_area, help="ink px; smaller blobs are ignored")
    g.add_argument("--pad", type=int, default=d.pad, help="px of margin around each crop")


def _add_read(p):
    p.add_argument("--reader", required=True, help="preset, mlx:<repo> or openai:<model> (see `readers`)")
    g = p.add_argument_group("reader")
    g.add_argument("--task-prompt", help="fixed prompt for OCR-style models, replaces the instruction")
    g.add_argument("--thinking", choices=["on", "off"], help="reasoning mode for models that have one")
    g.add_argument("--max-tokens", type=int, help="answer length limit")
    g.add_argument("--base-url", help="openai: server URL, e.g. http://localhost:11434/v1 (Ollama)")
    g.add_argument("--api-key-env", help="openai: environment variable holding the API key")


def build_parser():
    ap = argparse.ArgumentParser(prog="markpipe", description="Read pen-circled text on scanned pages.")
    ap.add_argument("-v", "--verbose", action="store_true", help="log every crop")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, help_, detect, read in (("detect", "find marks and cut crops", True, False),
                                      ("read", "read the crops of a previous detect run", False, True),
                                      ("run", "detect, then read", True, True)):
        p = sub.add_parser(name, help=help_)
        if detect:
            _add_detect(p)
        p.add_argument("--out", required=True, help="output folder")
        p.add_argument("--pages", help="comma list of page names, e.g. img_01,img_20")
        if read:
            _add_read(p)
    sub.add_parser("readers", help="list reader presets")
    return ap


def _reader_options(a):
    return dict(task_prompt=a.task_prompt, max_tokens=a.max_tokens, base_url=a.base_url, api_key_env=a.api_key_env,
                thinking=None if a.thinking is None else a.thinking == "on")


def _detect(a):
    cfg = DetectorConfig(diff_thresh=a.diff_thresh, gap=a.gap, min_area=a.min_area, pad=a.pad)
    for r in detect_pages(find_pairs(a.data, _csv(a.pages)), a.out, cfg):
        print(r.summary())


def _read(a):
    with create_reader(a.reader, **_reader_options(a)) as reader:
        rows = read_crops(a.out, reader, _csv(a.pages))
    for r in rows:
        print(f"{r['page']} #{r['id']}: {r['answer']!r}" + (f"  ({r['error']})" if r["error"] else ""))
    answered = [r["seconds"] for r in rows if r["answer"] is not None]
    print(f"{len(answered)}/{len(rows)} marks read, {sum(answered) / max(len(answered), 1):.2f} s/crop")


def main(argv=None):
    a = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if a.verbose else logging.WARNING, format="%(levelname)s %(message)s")
    try:
        if a.cmd == "readers":
            for name, (backend, _, desc) in PRESETS.items():
                print(f"{name:24s} {backend:9s} {desc}")
            print("\nAlso: mlx:<huggingface repo>, openai:<model> (with --base-url)")
        if a.cmd in ("detect", "run"):
            _detect(a)
        if a.cmd in ("read", "run"):
            _read(a)
    except (ReaderError, FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0
