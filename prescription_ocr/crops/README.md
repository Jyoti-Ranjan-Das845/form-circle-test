# Text crops: can the model read the handwriting itself?

24 small crops, 3 from each of the 8 prescriptions, each holding only text the human reader is sure of.
Use them to separate two problems: the model **cannot read** the handwriting, or it reads it but **puts it in the
wrong field** of the JSON.

- `images/<crop>.jpeg`: the crop, cut from `../images/<rxN>.jpeg` (names already masked)
- `ground_truth.json`: for each crop, the source image, the box (x0, y0, x1, y1 in pixels) and the text
- `score_crops.py`: checks every word and number of the text against the model's output

## Run

```bash
# GPU or Colab
python run.py --local --images crops/images --out results/local_crops
# Apple Silicon
python run_mlx.py crops/images results/mlx_crops
# then score (from prescription_ocr/)
python crops/score_crops.py results/mlx_crops
```

The model only takes a document tag, so the crops are read with `<prescription>` and come back as JSON. The scorer
looks for the text anywhere in that output, so a value counts as read even if it lands in the wrong field;
`110/82` also counts when it comes back as 110 and 82. Write the results back with `git add -f results`.

## What is written in each crop

Written as the prescriber wrote it. Shorthand is kept: `Bp` = blood pressure, `FBS` / `PPBS` = fasting / post-meal
sugar, `A1C` = HbA1c, `C/O` = complains of, `B/L` = both sides. Doctors often scrawl `Tab` so it looks like
`Tas` or `Tcs`. Trailing dots and dashes on the page are left out.

| crop | text |
|---|---|
| `rx1_a` | FBS. 146 / 2h. PPBS - 342 |
| `rx1_b` | Diabetic diet |
| `rx1_c` | Cap Myelobest |
| `rx2_a` | 71/F |
| `rx2_b` | 150/76 |
| `rx2_c` | Tab. Telx-3D |
| `rx3_a` | Bp - 110/82 mm |
| `rx3_b` | FBS - 180 / PPBS - 246 mg/dl |
| `rx3_c` | Cap PAN-D |
| `rx4_a` | Bp - 110/67 mmHg |
| `rx4_b` | Tab Glycomet SR 500 |
| `rx4_c` | Dyslipidemia |
| `rx5_a` | TG - 344 mg/dl / LDL - 134 mg/dl / FBS - 345 mg/dl / PPBS - 430 mg/dl |
| `rx5_b` | A1C - 10.2% / TSH - 8.56 / Creat - 0.53 / AST/ALT - 53/38 / Hb - 10.6 |
| `rx5_c` | Thyrox 37.5 |
| `rx6_a` | FBS - 152 / PPBS - 204 mg/dl |
| `rx6_b` | Bp - 138/84 mm |
| `rx6_c` | Cap Nurokind plus |
| `rx7_a` | Bp - 160/100 mm |
| `rx7_b` | Na+ - 135 |
| `rx7_c` | (2) Tab Telista H 40 |
| `rx8_a` | BP: 116/81 |
| `rx8_b` | C/O - calf pain (B/L) |
| `rx8_c` | 1) Tab. Etoshine-MR |
