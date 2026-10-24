"""Extract pages from the RVL-CDIP 100-per-class subset (real scanned documents).

Source: huggingface.co/datasets/jordyvl/rvl_cdip_100_examples_per_class (parquet splits).
Usage:  .venv/bin/python -I src/fetch_rvl.py <out_dir> <split.parquet>...
"""
import sys
from pathlib import Path

import pyarrow.parquet as pq

CLASSES = {0: "letter", 1: "form", 5: "sci_report", 6: "sci_pub", 7: "spec", 9: "news", 13: "questionnaire", 15: "memo"}

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
counts = {}
for path in sys.argv[2:]:
    split = Path(path).stem
    for i, row in enumerate(pq.read_table(path).to_pylist()):
        name = CLASSES.get(row["label"])
        if name:
            counts[name] = counts.get(name, 0) + 1
            (out / f"{name}_{split}_{i:04d}.tif").write_bytes(row["image"]["bytes"])
print(counts)
