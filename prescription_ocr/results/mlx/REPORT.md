# Parrotlet-v 2.5 Pro on rx1–rx8, local MLX 8-bit, 2026-11-12

Run with `prescription_ocr/run_mlx.py` on an M4 Mac, 24 GB: `ekacare/parrotlet-v-2.5-pro` converted to 8-bit MLX
(5.9 GB on disk, 8.3 GB peak memory), tag `<prescription>`, greedy, 2048 new tokens. Caveat: 8-bit weights, not
the bf16 on the model card, so small differences from a GPU run are possible.

`rxN.json` = plain greedy run. `rxN_reppen1.1.json` = rerun with repetition penalty 1.1 for the two pages that
misbehaved. Compared against the human readings in `prescription_ocr/README.md` and the photos.

| page | s | valid JSON | right | wrong / missing |
|---|---|---|---|---|
| rx1 | 18 | yes | BP 100/80; T2DM; 2h PPBS 342; Myelobest 1 OD; USG abdomen for pancreas morphology; S. creatinine; FBS; 2h PPBS; diabetic diet; insulin doses 18 → 4 captured as text | invented BodyWeight 3 kg and HeartRate 100; invented HTN and Hypothyroidism; FBS 146 labelled HbA1c; Doloneuron-NT → "Solonorm-NT", BD instead of after dinner, titration lost; insulin filed under advice; "fasting lipid profile" → "Fechity liver profile" |
| rx2 | 5 | yes | nothing usable | output is a single BodyWeight 71 kg (the age). No medicines, no vitals. Same with repetition penalty. The cut-off page makes the model give up rather than read what is visible |
| rx3 | 14 | yes | date; BP 110/82; Pan-D; 5 of 6 medicines present | sex, FBS 180, PPBS 246, "reluctant for insulin" missed; Myelohelp missing; four brand names garbled; doses nonsensical (7, 3 tablets); frequencies wrong; follow-up 2 weeks vs 1 month |
| rx4 | 10 | yes | BP 110/67 read as 110/87; 3 medicine lines | insulin (Lupisulin M30, 14/8 units) missing entirely; Glycomet SR 500 → "Linagliptin 480"; Calcimed → "Calcirol 500"; Rosuhelp 10 → "Risenat 40"; every frequency 1-0-1 × 1 month, which is not on the page; impression, dyslipidemia and all advised tests missed |
| rx5 | 18 | yes | date; BP 126/86 read as 126/96; TSH 8.56; creatinine 0.53; AST/ALT 53/38; all 5 medicine lines present; Thyrox 37.5 → "Trox 37.5"; Glimisave MV 2.2 → "Glimepiride MV 2.2" (generic swap); Loyfor XL ok | HbA1c 10.2 labelled Hb%; TG 344, LDL 134, FBS 345, PPBS 430, Hb 10.6 missed; the struck-out name handled (took the rewritten one) but as "Sanifran 1000"; Rosuhelp → "Rosmelp"; every frequency 1-0-1 and durations invented; advised tests reduced to Hb% |
| rx6 | 15 | yes | date; BP 138/84 read as 138/89; all 7 items present as lines; before/after-meal timing roughly right | names mostly garbled (Geminor M2 Forte → "Geminut 1000", Nurokind Plus → "Neurokind 10mg", Rosuhelp 10 → "Rosnhiem 20", Rexidin M Forte gel → "Raxidi Mefoli" as a tablet, Bifolate → "Brifolac"); FBS 152, PPBS 204, T2DM × 9 y, glossitis, durations all missed; every frequency 1-0-1 |
| rx7 | 60 / 25 | no / yes | BP 160/100; HbA1c 7.1; creatinine; LDL 102 (as "Lox"); TSH 4.19; Nicardia Retard 20, Telista H 40, Met XL present | plain run looped on "S. Na / S. K" until the token cap, JSON invalid; with repetition penalty 1.1 it finishes: Na 135 and K 4.48 appear but also invented Na 128, K 198, Na 240 and other junk lab rows; Met XL 25 → 75; Rosuhelp and Oma Q10 lost; USG hepatomegaly missed; every frequency 1-0-1 |
| rx8 | 12 | yes | BP 116/81; calf pain B/L since 6 days; all 5 medicines; BD / OD / once weekly / 3 months; Susrab-DSR exact | Etoshine-MR → "Etospine-MR", Myelohelp → "Myelofelp", Uprise-D3 → "Upze-D3"; gel → "Flunazenz" with invented 10-day duration; ×10 d and ×30 d durations dropped |

## Summary
- Usable on 1 of 8 pages without correction (rx8, the clean printed form). Partly usable on rx1, rx5, rx7.
  Poor on rx3, rx4, rx6. Nothing on rx2.
- Reliable: BP (though the diastolic digit was misread on 3 pages), dates, the count of medicine lines,
  before/after-food timing when written plainly.
- Unreliable: handwritten brand names (1–3 letters off on most, sometimes a different drug), lab panels
  written as a row (values dropped or mislabelled, HbA1c ↔ Hb%), durations and titrations.
- Dangerous failure modes: it fills frequency with 1-0-1 and duration with 1 month when it cannot read
  them, instead of leaving the field empty; it invents vitals (weight 3 kg) and lab rows (rx7); on a cut-off
  page it returns almost nothing rather than the visible part; on a dense page it can loop until the token
  cap (rx7), so a repetition penalty or a loop stop is needed in production.
- Speed and memory on the Mac are not a problem: 5–25 s per page, 8.3 GB peak.
