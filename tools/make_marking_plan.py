"""Rebuild marking_plan.md (what to circle on each page) from data/ground_truth/*.json.

Usage:  python tools/make_marking_plan.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def show(v):
    if v is None:
        return "(none — leave blank)"
    if isinstance(v, list):
        return " · ".join(v)
    return v


def main():
    lines = ["# Marking plan", "",
             "Circle each item in red on the page in `real_forms_marked/`. `Expected` is what a correct pipeline must return.",
             "This file is generated from `data/ground_truth/` — edit those files, then rerun `python tools/make_marking_plan.py`.", ""]
    for path in sorted((ROOT / "data" / "ground_truth").glob("*.json")):
        g = json.loads(path.read_text())
        lines += [f"## {g['image']}", "", "| # | Where | How | Expected |", "|---|---|---|---|"]
        for it in g.get("items", []) + g.get("answers", []):
            exp = it["text"] if g["kind"] == "text" else it["expected"]
            cells = [it["id"], it["where"], it["how"], show(exp)]
            lines.append("| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |")
        lines.append("")
    (ROOT / "marking_plan.md").write_text("\n".join(lines))
    print("wrote marking_plan.md")


if __name__ == "__main__":
    main()
