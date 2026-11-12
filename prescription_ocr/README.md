# Prescription OCR test: parrotlet-v-2.5-pro

Eight handwritten Indian prescriptions, photographed on a phone, read by Eka Care's open vision model
[`ekacare/parrotlet-v-2.5-pro`](https://huggingface.co/ekacare/parrotlet-v-2.5-pro) with the `<prescription>` tag.
**Patient names are blacked out.**

| Image | What makes it easy or hard |
|---|---|
| `images/rx1.jpeg` | Endocrinologist, insulin dose arrows, labs and advised tests on the page |
| `images/rx2.jpeg` | Right side and bottom **cut off**; dose columns and the last medicine partly missing |
| `images/rx3.jpeg` | Taken at an angle, thumb over the margin, six brand-name combination drugs |
| `images/rx4.jpeg` | Torn top edge, fingers on the margin, insulin doses |
| `images/rx5.jpeg` | A medicine name **struck out** and rewritten; a long row of lab values |
| `images/rx6.jpeg` | Strong tilt, left margin cut off, another letterhead visible underneath; seven items |
| `images/rx7.jpeg` | No letterhead (lower half of a page), heavy shadow, many lab values |
| `images/rx8.jpeg` | Easiest: neat cursive, printed form, bilingual (English / Odia) letterhead |

## Run it

**Option A: on a machine with an NVIDIA GPU (≥ 12 GB VRAM)** or a free Google Colab T4. The model downloads once
(~11 GB).

```bash
git clone https://github.com/Jyoti-Ranjan-Das845/form-circle-test.git
cd form-circle-test/prescription_ocr
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py --local
```

**Option B: no GPU, use Featherless** (hosted, OpenAI-compatible API):

```bash
pip install requests
export FEATHERLESS_API_KEY=your_key_here
python run.py --featherless
```

Run some images only: `python run.py --local rx3 rx8`.

Each result is saved to `results/<local|featherless>/<image>.json`: the raw model output, the parsed JSON, the
time taken and the token counts. `results/` is git-ignored in this repo; to push the results back, run
`git add -f results && git commit -m "parrotlet results" && git push`.

## What a human read on each page (to compare against)

`~` = likely reading, `?` = unclear to the human reader too. These are not verified ground truth either;
disagreements are worth checking against the image.

**rx1**: BP 100/80 · FBS 146 · 2h PPBS 342 · K/c/o T2DM (4 y), non-smoker, DSPN
1. Diabetic diet
2. Regular exercise, 30 min a day
3. Inj. Insugen (30/70): 18 units before breakfast → 4 units before dinner ~, 30 min before food
4. Tab Doloneurom-NT (200/10) ?: ½ tab after dinner × 6 days, then 1 tab after dinner × 1 month
5. Cap Myelobest ~: 1 after dinner

Advised: USG abdomen & pelvis (pancreas morphology), Sr. creatinine, fasting lipid profile, FBS, 2h PPBS

**rx2**: Age 71 · F · C/O palpitation with giddiness · left notes cut off: two findings "+ve", 6.3 (~HbA1c),
96 and 134 (~sugars), BP 150/76 ~
1. Tab Telx-3D ?: 1×1×30 (cut off)
2. Tab Sugita DM-500 ?: 1×1… (cut off)
3. Tab Roscenava + CV ?
4. Tab Pentanerve GPX ? (cut off)

**rx3**: Date 3/10/26 · Sex M · BP 110/82 · FBS 180 · PPBS 246 mg/dl · K/c/o T2DM ~ · "Reluctant for insulin"
1. Tab Glimisave MV 2.2 ~: 1 before breakfast
2. Tab Cospiaq SM 25/1000 ?: 1 before breakfast ~
3. Tab Geminor M4 ?: 1 before meal ?
4. Tab Rosuhelp 10 ~: 1 at night ~
5. Tab Myelohelp ~: 1 after … ?
6. Cap PAN-D: 1 before breakfast × 10 days ~

Advised: FBS, 2h PPBS after 1 month

**rx4**: Date 3/10/26 · F · 30 y · Impression ? Type 3c DM ~ (abdominal pain) ~ · dyslipidemia · BP 110/67
1. Inj. Lupisulin M30 ~: 14 units before breakfast, 8 units before dinner ~
2. Tab Glycomet SR 500: 1 after breakfast ~
3. Tab Calcimed XL ?: 1 after (lunch?) ?
4. Tab Rosuhelp 10 ~: 1 after dinner ~

Advised (after 1 month): FBS, 2h PPBS, urea, creatinine, fasting lipid profile, USG abdomen & pelvis
(pancreatic pathology)

**rx5**: Date 3/10/26 · F · 47 y ~ · T2DM × 2 months, SCH, ? MASLD · O/E ? grade Ib goitre ~ · BP 126/86 ·
TG 344 · LDL 134 · FBS 345 · PPBS 430 · HbA1c 10.2% · TSH 8.56 · Creat 0.53 · AST/ALT 53/38 · Hb 10.6
1. Tab SHLT-D Trio 1000 ? (written above a crossed-out name): 1 after food
2. Tab Glimisave MV 2.2 ~: 1 before breakfast ~
3. Tab Thyrox 37.5: 1 before breakfast, empty stomach
4. Tab Rosuhelp 10 ~: 1 after dinner
5. Tab Loyfor XL ?: 1 after dinner ?

Advised (after 1 month): FBS, 2h PPBS, AST/ALT, Hb%, TSH, fasting lipid profile, diet and exercise ·
circled note ~"Endocrinology review" ?

**rx6**: Date 3/10/26 · F · 58 y · T2DM × 9 years, dyslipidemia · O/E atrophic glossitis · BP 138/84 · FBS 152 ·
PPBS 204 mg/dl
1. Tab Geminor M2 Forte ?: 1 before breakfast ~
2. Tab S?nta SM 1000 ?: 1 after meal ?
3. Cap Nurokind Plus ~: 1 after meal ?
4. Tab Pregal… NT ?: 1 OD
5. Tab Rosuhelp 10 ~: 1 after dinner ~
6. Rexidin M Forte ~ gel ?: local application twice a day × 1 week ~
7. Tab Bifolate ~: 1 OD × 2 months

Advised: tests after 1 month (margin cut off; lipid profile visible), diet and exercise, ~"… dental / eye exam" ?

**rx7**: Date 3/10/26 · no patient details on this part · ? T2DM (word in brackets unclear) · BP 160/100 ·
FBS 128 · PPBS 198 · HbA1c 7.1% · Na⁺ 135 · K⁺ 4.48 · Creat 0.61 ~ · LDL 102 · TSH 4.19 ·
USG: hepatomegaly with moderate fatty change
1. Tab Nicardia Retard 20: 1 BD
2. Tab Telista H 40: 1 before breakfast ~
3. Tab Met XL 25 ~: 1 after (night?) ?
4. Tab Rosuhelp 10 ~: 1 after dinner ~
5. Cap Oma Q10 ?: 1 after dinner ?

Advised: FBS, 2h PPBS, Na⁺, K⁺, AST, ALT, ~"Cardiology consult", diet and exercise,
~"Gen. surgery to evaluate for hernia" ?

**rx8**: Date 4/10/26 · BP 116/81 · C/O calf pain (both sides) since 6 days
1. Tab Etoshine-MR: 1 BD after food × 10 days
2. Tab Myelohelp: 1 OD after food × 30 days
3. Tab Uprise-D3: 1 once weekly for 3 months
4. Cap Susrab-DSR: 1 OD before food × 10 days
5. Flenabenz ? Gel: local application BD
