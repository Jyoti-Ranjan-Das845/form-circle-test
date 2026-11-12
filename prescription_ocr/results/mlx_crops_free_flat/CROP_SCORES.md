# Crop text check

Results: `mlx_crops_free_flat/` · ground truth: `crops/ground_truth.json`

**Crops fully read: 2/24** · words and numbers found: 32/85 (38%)

| crop | written on the page | found | missing | model output (start) |
|---|---|---|---|---|
| rx1_a | FBS. 146 / 2h. PPBS - 342 | 3/5 | fbs, ppbs | `HBs. 146 2h. PPD - 342` |
| rx1_b | Diabetic diet | 2/2 |  | `Diabetic diet` |
| rx1_c | Cap Myelobest | 0/2 | cap, myelobest | `"Co p Nyelobest"` |
| rx2_a | 71/F | 0/1 | 71/f | `"F"` |
| rx2_b | 150/76 | 0/1 | 150/76 | `150` |
| rx2_c | Tab. Telx-3D | 1/2 | telx-3d | `Tab.` |
| rx3_a | Bp - 110/82 mm | 2/3 | bp | `"P1 - 110/82 mmHg"` |
| rx3_b | FBS - 180 / PPBS - 246 mg/dl | 0/5 | fbs, 180, ppbs, 246, mg/dl | `"foc - 1500"` |
| rx3_c | Cap PAN-D | 1/2 | pan-d | `"cap p.AN-D"` |
| rx4_a | Bp - 110/67 mmHg | 0/3 | bp, 110/67, mmhg | `"30° - 110° (mm)"` |
| rx4_b | Tab Glycomet SR 500 | 1/4 | tab, glycomet, 500 | `"Gylcomet SR"` |
| rx4_c | Dyslipidemia | 0/1 | dyslipidemia | `"m liquid"` |
| rx5_a | TG - 344 mg/dl / LDL - 134 mg/dl / FBS - 345 mg/dl / PPBS - 430 mg/dl | 5/12 | tg, ldl, 134, fbs, 345, ppbs, 430 | `"TK - 344 mg/dl"` |
| rx5_b | A1C - 10.2% / TSH - 8.56 / Creat - 0.53 / AST/ALT - 53/38 / Hb - 10.6 | 6/10 | a1c, tsh, ast/alt, hb | `"↑↑↑ 10.2%." "↑↑↑ 8.56" "Creat - 0.53" "↑↑↑ 53/38." "↑↑↑ 10.6"` |
| rx5_c | Thyrox 37.5 | 1/2 | thyrox | `"37.5"` |
| rx6_a | FBS - 152 / PPBS - 204 mg/dl | 1/5 | fbs, ppbs, 204, mg/dl | `"fx - 152"` |
| rx6_b | Bp - 138/84 mm | 1/3 | bp, 138/84 | `"38/84 mm"` |
| rx6_c | Cap Nurokind plus | 0/3 | cap, nurokind, plus | `"Neurokind"` |
| rx7_a | Bp - 160/100 mm | 1/3 | bp, mm | `"000 160/100 000"` |
| rx7_b | Na+ - 135 | 1/2 | 135 | `Na+125` |
| rx7_c | (2) Tab Telista H 40 | 0/5 | 2, tab, telista, h, 40 | `"1kg 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000` |
| rx8_a | BP: 116/81 | 2/2 |  | `BP: 116 / 81` |
| rx8_b | C/O - calf pain (B/L) | 3/4 | pain | `C/O calf perianal (B/L)` |
| rx8_c | 1) Tab. Etoshine-MR | 1/3 | 1, etoshine-mr | `"Tab. Etosline-MPR"` |
