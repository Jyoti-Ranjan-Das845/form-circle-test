# Circle-mark pipeline: subtract, box, crop, read

Tested end to end: 38/38 circled items recovered by Qwen3.5-9B and 38/38 by PaddleOCR-VL on the
inside-only crops (see result tables below). Files:
- `extract_markers.py`  deterministic detector: marked page minus clean page -> one box + 3 crops per mark
- `run_crops.py`        send each crop to an mlx-vlm model (Qwen3.5-9B/4B, PaddleOCR-VL, GLM-OCR)
- `run_crops_ocr.py`    same crops through tesseract / RapidOCR / Apple Vision
- `score_crops.py`      score answers against data/ground_truth
- `test_edge_cases.py`  synthetic edge cases (gap, missing arc, double loop, touching circles, tick, blue ink)
- `out/`                detector output per page; `out_vlm/`  model answers; `out_edge_cases/`  overlays

Requirements: Python 3.12, numpy, pillow, opencv-python, scikit-image; mlx-vlm for run_crops.py;
tesserocr + rapidocr-onnxruntime + ocrmac for run_crops_ocr.py (Apple Silicon).


`extract_markers.py` subtracts each clean page from its marked copy and turns every pen mark
into a bounding box plus three crops. Runs in about a second for all 20 pages.

```
.venv_vlm/bin/python experiments/marker_crops/extract_markers.py            # all pages, defaults
.venv_vlm/bin/python experiments/marker_crops/extract_markers.py --pages 04,20 --gap 8 --pad 6 --min-area 40 --diff-thresh 30
```

## Pipeline
1. Flatten RGBA over white, subtract clean page, keep pixels whose max channel change > `diff-thresh`
   (colour-agnostic, so dark pixels where red ink crosses black text are kept too).
2. 3x3 close to heal anti-alias holes; dilate by `gap` px to bridge stroke gaps; 8-connected components.
3. Per component: tight box from the undilated ink, ink pixel count, mean colour, red fraction,
   number of enclosed holes (1 = closed circle, 0 = open stroke, 2+ = two circles merged).
4. Crops with `pad` px margin, same pixel coordinates as the original page:
   - `marker_NN_marked.png` from the marked page
   - `marker_NN_clean.png` from the clean page
   - `marker_NN_inside.png` clean page with everything outside the circle interior whitened
5. `overlay.png` (green = closed, orange = open, blue = merged?), `ink_only.png`, `markers.json`, `out/summary.json`.

## Edge cases handled (verified by `test_edge_cases.py`, synthetic marks drawn on page 01)
| case | mechanism | result |
|---|---|---|
| RGBA marked page | flattened on white before subtraction | ok |
| size mismatch / no clean twin | reported, page skipped | ok |
| page with no ink (13 placeholders) | reported as unmarked | ok |
| anti-alias specks | blobs under `min-area` ink px dropped | ok |
| small break in the stroke (10 px gap) | skeleton endpoints closer than 2x`gap` are joined by a line, so the interior is still enclosed; no big morphological close, so small circles keep their interior | 1 box, closed, inside crop |
| large missing arc (40 % of circle) | no enclosed interior | 1 box around the remaining arc, `open`, no inside crop |
| user goes round twice at a larger radius | ring pieces are "thin" (distance transform <= 4 px) and attach to the fat interior they touch; a cluster whose box encloses another swallows it | 1 box, closed, note `double stroke` |
| two circles touching / overlapping | two fat interiors never merge; ink is assigned to the nearest interior | 2 boxes, note `split` |
| tick / underline | no interior | 1 box, `open`, no inside crop |
| blue (non-red) ink | detection is by change, colour only recorded | 1 box, `red_fraction` 0.0 |
| marker at the page edge | crop padding clamped | ok |

## Result on this dataset (defaults)
| page | markers | answer-key items | note |
|---|---|---|---|
| 01 | 4 | 4 | |
| 02 | 5 | 5 | |
| 03 | 6 | 6 | |
| 04 | 6 | 6 | two-column page |
| 05 | 5 | 5 | |
| 06 | 7 | 7 | |
| 20 | 5 | 6 | item q1_2_3 has expected null, i.e. deliberately unmarked |
| 07-19 | 0 | - | unmarked placeholders |

38 crops, all closed circles, every crop contains its answer-key item (see `out/contact_sheet.png`).
Counts are identical for `--gap` 2..8 and `--diff-thresh` 15..100; gap 12+ starts merging neighbours.

## VLM on the crops: Qwen3.5-9B (4-bit), 2026-11-01
`run_crops.py qwen35_9b --modes marked,both,inside`, scored by `score_crops.py`. 38 crops.

| input per crop | prompt | hit /38 | exact /38 | s/crop |
|---|---|---|---|---|
| marked crop only | what text is inside the red circle | 38 | 37 | 0.9 |
| marked crop + clean crop | same, two images | 38 | 35 | 1.4 |
| inside-only crop (no ink) | what text is in this image | 38 | 38 | 0.9 |

hit = answer-key item contained in the answer; exact = answer is the item (punctuation ignored).
Non-exact answers only carried a neighbouring character into the answer: "Circulation K", "Boston U",
": MARCH 11, 1996", "f toxic waste,", "-SMOKERS!". Compare whole-page circled prompt: 27/38.

## Direct OCR engines on the same crops, 2026-11-01
`run_crops.py paddle_vl` (mlx-vlm, prompt `OCR:`) and `run_crops_ocr.py` (crops upscaled 3x; tesseract 5.5
via tesserocr wheel + tessdata_fast eng, RapidOCR = PP-OCR ONNX models, Apple Vision via ocrmac).
OCR engines cannot be told "inside the circle", so on the marked and clean crops they transcribe the whole
rectangle including neighbouring-line slivers; the inside-only crop is the fair test.

| engine | inside-only hit /38 | inside exact /38 | marked crop hit /38 | clean crop hit /38 | s/crop |
|---|---|---|---|---|---|
| Qwen3.5-9B 4-bit (VLM) | 38 | 38 | 38 | - | 0.9 |
| PaddleOCR-VL 1.6 4-bit | 38 | 37 | 35 | 38 | 0.3 |
| tesseract 5.5 | 33 | 32 | 21 | 35 | 0.02 |
| RapidOCR (PP-OCRv4) | 32 | 31 | 29 | 32 | 0.15 |
| Apple Vision | 30 | 30 | 31 | 33 | 0.05 |

Inside-crop misses: tesseract blank on 03 #1/#6, "$1Y billion", "Buston", "yo" for NO; RapidOCR "unobtruaive",
"50-1iter", blank on 03 #1, "OK" for NO; Apple Vision "Germant own", "50-1iter", "Baston", blanks, "OK"/"wI" for NO/3.
Red ink crossing the glyphs costs the classic engines most on the marked crop (tesseract 21/38). PaddleOCR-VL
is the only OCR model close to the VLM, and it is 3x faster and 0.7 GB. All weights purged after the run.
