# Parrotlet-v 2.5 Pro on the 24 ground-truth crops, local MLX 8-bit, 2026-11-12

Crops: `prescription_ocr/crops/images` (3 per prescription, 50–105 px tall), truth: `crops/ground_truth.json`.
Model: `ekacare/parrotlet-v-2.5-pro` converted to 8-bit MLX, greedy, on an M4 Mac (8.3 GB peak, ~4 s per crop per prompt).

Two prompts were tried on every crop:

| prompt | results folder | crops fully read | words + numbers found | notes |
|---|---|---|---|---|
| `<prescription>` tag, as run.py does | `mlx_crops/` (scored by `crops/score_crops.py` → `CROP_SCORES.md`) | 0 / 24 | 11 / 85 (13%) | 21 of 24 crops return the empty schema `{"prescription_elements": {}}`. Only rx1_a, rx5_a, rx5_b, which look like a lab row, produce any fields |
| free prompt "Transcribe all the text in this image exactly as written" | `mlx_crops_free/` (per-crop JSON with CER / WER / word F1, `RESULTS.md`) and `mlx_crops_free_flat/` (same raw text in run.py layout, scored → `CROP_SCORES.md`) | 2 / 24 | 32 / 85 (38%) | mean CER 2.6 (one crop looped on zeros; without it ~0.5), mean word F1 21% |

## What the free prompt actually read (GT → model)
- Exact: `Diabetic diet`; `BP: 116/81` (as "BP: 116 / 81").
- Close: `FBS. 146 / 2h. PPBS - 342` → "HBs. 146 / 2h. PPD - 342"; `Bp - 110/82 mm` → "P1 - 110/82 mmHg"; `Cap PAN-D` → "cap p.AN-D";
  `Tab Glycomet SR 500` → "Gylcomet SR"; `C/O - calf pain (B/L)` → "C/O calf perianal (B/L)"; `1) Tab. Etoshine-MR` → "Tab. Etosline-MPR";
  `Cap Nurokind plus` → "Neurokind"; `Cap Myelobest` → "Co p Nyelobest".
- Numbers kept, labels lost: `TSH 8.56 / Creat 0.53 / AST/ALT 53/38 / Hb 10.6` → values right, every label except Creat became "↑↑↑";
  `Thyrox 37.5` → "37.5"; `150/76` → "150"; `Bp - 138/84` → "38/84".
- Wrong: `71/F` → "F"; `Dyslipidemia` → "m liquid"; `Bp - 110/67 mmHg` → "30° - 110° (mm)"; `FBS - 180 / PPBS - 246` → "foc - 1500";
  `Na+ - 135` → "Na+125"; `Tab. Telx-3D` → "Tab."; `(2) Tab Telista H 40` → a string of zeros until the token cap.

## Reading
- The tag mode is the wrong tool for a crop: the model was trained on whole prescriptions and returns an empty schema when the image does not look like one. Scoring the tag on crops measures that mismatch, not handwriting reading.
- The free prompt shows what the model can actually see: numbers are read fairly well (BP and lab values mostly right), handwritten words are usually
  1–3 letters off, and labels written as abbreviations (FBS, PPBS, Bp, TSH) are the weakest. This matches the full-page runs, where vitals were
  reliable and drug names were not.
- Crop height of 50–105 px is low for handwriting. The processor upscales to its patch budget, but no detail is added. Crops at 2–3× the resolution
  from the original photo would be a fairer test of the model than these downscaled cuts; the full pages gave better readings of the same text
  (e.g. "Cap. Myelobest", "Tab. Etospine-MR", "Dyslipidemia" was missed on both).
- The zero-loop on rx7_c is the same failure seen on the rx7 page; a repetition penalty or loop stop is needed before any production use.
