# Crop text check

Results: `mlx_crops/` · ground truth: `crops/ground_truth.json`

**Crops fully read: 0/24** · words and numbers found: 11/85 (13%)

| crop | written on the page | found | missing | model output (start) |
|---|---|---|---|---|
| rx1_a | FBS. 146 / 2h. PPBS - 342 | 1/5 | fbs, 2h, ppbs, 342 | `{"prescription_elements": {"diagnosticResults": [{"category": "laboratory", "name": "HBsAg", "results": [{"name": "HBsAg", "value": 146}]}]}}` |
| rx1_b | Diabetic diet | 0/2 | diabetic, diet | `{"prescription_elements": {}}` |
| rx1_c | Cap Myelobest | 0/2 | cap, myelobest | `{"prescription_elements": {}}` |
| rx2_a | 71/F | 0/1 | 71/f | `{"prescription_elements": {}}` |
| rx2_b | 150/76 | 0/1 | 150/76 | `{"prescription_elements": {}}` |
| rx2_c | Tab. Telx-3D | 0/2 | tab, telx-3d | `{"prescription_elements": {}}` |
| rx3_a | Bp - 110/82 mm | 0/3 | bp, 110/82, mm | `{"prescription_elements": {}}` |
| rx3_b | FBS - 180 / PPBS - 246 mg/dl | 0/5 | fbs, 180, ppbs, 246, mg/dl | `{"prescription_elements": {}}` |
| rx3_c | Cap PAN-D | 0/2 | cap, pan-d | `{"prescription_elements": {}}` |
| rx4_a | Bp - 110/67 mmHg | 0/3 | bp, 110/67, mmhg | `{"prescription_elements": {}}` |
| rx4_b | Tab Glycomet SR 500 | 0/4 | tab, glycomet, sr, 500 | `{"prescription_elements": {}}` |
| rx4_c | Dyslipidemia | 0/1 | dyslipidemia | `{"prescription_elements": {}}` |
| rx5_a | TG - 344 mg/dl / LDL - 134 mg/dl / FBS - 345 mg/dl / PPBS - 430 mg/dl | 6/12 | tg, ldl, fbs, 345, ppbs, 430 | `{"prescription_elements": {"medicationRequest": [{"name": "T.K", "frequency": "3-4-4", "note": "mg/dl"}, {"name": "L.M", "frequency": "1-3-4", "note": "mg/dl"},` |
| rx5_b | A1C - 10.2% / TSH - 8.56 / Creat - 0.53 / AST/ALT - 53/38 / Hb - 10.6 | 3/10 | a1c, 10.2, tsh, 8.56, ast/alt, hb, 10.6 | `{"prescription_elements": {"diagnosticResults": [{"category": "laboratory", "name": "Creat", "results": [{"name": "Creat", "value": 0.53}]}, {"category": "labor` |
| rx5_c | Thyrox 37.5 | 0/2 | thyrox, 37.5 | `{"prescription_elements": {}}` |
| rx6_a | FBS - 152 / PPBS - 204 mg/dl | 0/5 | fbs, 152, ppbs, 204, mg/dl | `{"prescription_elements": {}}` |
| rx6_b | Bp - 138/84 mm | 0/3 | bp, 138/84, mm | `{"prescription_elements": {}}` |
| rx6_c | Cap Nurokind plus | 0/3 | cap, nurokind, plus | `{"prescription_elements": {}}` |
| rx7_a | Bp - 160/100 mm | 0/3 | bp, 160/100, mm | `{"prescription_elements": {}}` |
| rx7_b | Na+ - 135 | 0/2 | na, 135 | `{"prescription_elements": {}}` |
| rx7_c | (2) Tab Telista H 40 | 0/5 | 2, tab, telista, h, 40 | `{"prescription_elements": {}}` |
| rx8_a | BP: 116/81 | 0/2 | bp, 116/81 | `{"prescription_elements": {}}` |
| rx8_b | C/O - calf pain (B/L) | 1/4 | calf, pain, b/l | `{"prescription_elements": {}}` |
| rx8_c | 1) Tab. Etoshine-MR | 0/3 | 1, tab, etoshine-mr | `{"prescription_elements": {}}` |
