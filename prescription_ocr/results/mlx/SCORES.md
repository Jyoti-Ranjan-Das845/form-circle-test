# Scores: parrotlet-v-2.5-pro vs human reading

Results: `mlx/` · ground truth: `eval/ground_truth.json` (the README readings; not verified by the prescriber). Regenerate with `python prescription_ocr/eval/score.py prescription_ocr/results/mlx`.

Exact-match scores use only readings the human was sure of. **Name CER** = character error rate on medicine names (0 = exact, 1 = nothing right). **Meds found** = an output line aligned to that page line (in order, names at least 25% alike); its name can still be wrong. **Invented** = vitals, lab rows, medicine lines and durations in the output that are not on the page.

## Per page

| run | JSON | BP | date | labs right | labs mislabelled | meds found | names exact | name CER | times/day | duration | tests | invented |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rx1 | ok | 2/2 | 0/– | 1/2 | 1 | 2/3 | 1/2 | 0.0 | 1/3 | 1/2 | 4/5 | 2 |
| rx2 | ok | 0/2 | 0/– | 0/0 | 0 | 0/4 | 0/0 | – | 0/0 | 0/0 | 0/0 | 1 |
| rx2_reppen1.1 | ok | 0/2 | 0/– | 0/0 | 0 | 0/4 | 0/0 | – | 0/0 | 0/0 | 0/0 | 1 |
| rx3 | ok | 2/2 | 1/1 | 0/2 | 0 | 5/6 | 1/4 | 0.29 | 0/6 | 0/6 | 0/2 | 4 |
| rx4 | ok | 1/2 | 0/1 | 0/0 | 0 | 3/4 | 0/3 | 0.77 | 1/4 | 0/4 | 0/6 | 3 |
| rx5 | ok | 1/2 | 1/1 | 1/9 | 3 | 5/5 | 0/3 | 0.27 | 0/5 | 0/5 | 1/6 | 5 |
| rx6 | ok | 1/2 | 1/1 | 0/2 | 0 | 7/7 | 0/4 | 0.44 | 1/7 | 5/7 | 0/1 | 0 |
| rx7 | **invalid** | 0/2 | 0/1 | 0/6 | 0 | 0/5 | 0/4 | – | 0/5 | 0/5 | 0/5 | 0 |
| rx7_reppen1.1 | ok | 2/2 | 0/1 | 2/6 | 4 | 5/5 | 1/4 | 0.19 | 1/5 | 5/5 | 0/5 | 7 |
| rx8 | ok | 2/2 | 0/1 | 0/0 | 0 | 5/5 | 1/4 | 0.15 | 5/5 | 1/5 | 0/0 | 1 |

Rows with a suffix are reruns (repetition penalty 1.1) and are not in the totals below.

## Totals, plain runs rx1–rx8

| field | right | |
|---|---|---|
| BP values | 9/16 (56%) | |
| document date | 3/6 (50%) | |
| lab name + value | 2/21 (10%) | 4 more had the right value under the wrong name |
| medicine lines found | 27/39 (69%) | |
| medicine name exact | 3/24 (12%) | mean name CER 0.32 |
| times per day | 8/35 (23%) | |
| duration | 7/34 (21%) | 13 durations not on the page |
| advised tests | 5/25 (20%) | |
| invented items | 16 | vitals, lab rows, medicine lines, durations |

## How each medicine line was matched, and what went wrong

**rx1**: Doloneurom-NT 200/10 → Tab. Solonorm-NT (200/10); Myelobest → Cap. Myelobest
  
_vitals not on page: BodyWeight 3, HeartRate 100 · FBS 146 labelled 'HbA1c' · medicines missed: Insugen 30/70_

**rx2**: no medicines in output
  
_vitals not on page: BodyWeight 71 · medicines missed: Telx-3D, Sugita DM-500, Roscenava CV, Pentanerve GPX_

**rx2_reppen1.1**: no medicines in output
  
_vitals not on page: BodyWeight 71 · medicines missed: Telx-3D, Sugita DM-500, Roscenava CV, Pentanerve GPX_

**rx3**: Glimisave MV 2.2 → Tab. Glimirs MN 2.25; Cospiaq SM 25/1000 → Tab. Cospirol 35/100; Geminor M4 → Tab. Geminos 40; Rosuhelp 10 → Tab. Rozonel 10; PAN-D → Cap. Pan-D
  
_medicines missed: Myelohelp_

**rx4**: Lupisulin M30 → Tab. Linagliptin 480; Calcimed XL → Tab. Calcirol 500; Rosuhelp 10 → Tab. Risenat 40
  
_medicines missed: Glycomet SR 500_

**rx5**: SHLT-D Trio 1000 → Tab. Sanifran 1000; Glimisave MV 2.2 → Tab. Glimepiride MV 2.2; Thyrox 37.5 → Tab. Trox 37.5; Rosuhelp 10 → Tab. Rosmelp 10; Loyfor XL → Tab. Loy for XL
  
_HbA1c 10.2 labelled 'Hb%' · TSH 8.56 labelled 'TS1' · AST/ALT 53/38 labelled 'TS1/ALT'_

**rx6**: Geminor M2 Forte → Tab. Geminut 1000; Santa SM 1000 → Tab. Sunita Duo; Nurokind Plus → Tab. Neurokind 10mg; Pregal NT → Tab. Pregaloy NT; Rosuhelp 10 → Tab. Rosnhiem 20; Rexidin M Forte → Tab. Raxidi Mefoli; Bifolate → Tab. Brifolac

**rx7**: no medicines in output
  
_medicines missed: Nicardia Retard 20, Telista H 40, Met XL 25, Rosuhelp 10, Oma Q10_

**rx7_reppen1.1**: Nicardia Retard 20 → Tab Nicandhia Retard 20; Telista H 40 → Tab Telista H 40; Met XL 25 → Tab Met XL 75; Rosuhelp 10 → Tab Ronnehip 10; Oma Q10 → Cap OMA Q10
  
_FBS 128 labelled 'Na+' · PPBS 198 labelled 'K+' · HbA1c 7.1 labelled 'A/C' · LDL 102 labelled 'Lox' · lab values not on page: VSK 104.5, Med. 29, Na+ 240, Ca 10.2, Al 1.3, Ca 10.2, Al 1.3_

**rx8**: Etoshine-MR → Tab. Etospine-MR; Myelohelp → Tab. Myelofelp; Uprise-D3 → Tab. Upze-D3; Susrab-DSR → cap. Susrab-DSR; Flenabenz Gel → Flunazenz Gel
