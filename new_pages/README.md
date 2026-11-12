# New test pages

Put each page in both folders with the SAME file name:

- `new_pages/clean/<name>.png`   the page without any pen marks
- `new_pages/marked/<name>.png`  the same page with the circles drawn (same pixel size)

PNG, JPG or TIFF. Then run from the repo root:

```
.venv_vlm/bin/python experiments/marker_crops/extract_markers.py --clean-dir new_pages/clean --marked-dir new_pages/marked --out experiments/marker_crops/out_new
.venv_vlm/bin/python experiments/marker_crops/run_crops.py parrotlet_v --modes marked,inside --in experiments/marker_crops/out_new --out experiments/marker_crops/out_vlm_new/parrotlet_v
```
