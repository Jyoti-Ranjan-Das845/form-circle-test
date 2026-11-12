# Prescription OCR test: parrotlet-v-2.5-pro

Three handwritten Indian prescriptions, photographed on a phone, read by Eka Care's open vision model
[`ekacare/parrotlet-v-2.5-pro`](https://huggingface.co/ekacare/parrotlet-v-2.5-pro) with the `<prescription>` tag.
**Patient names are blacked out.**

| Image | Why it is in the set |
|---|---|
| `images/rx1.jpeg` | Endocrinologist, insulin dose arrows, labs and advised tests on the page |
| `images/rx3.jpeg` | Hard: taken at an angle, thumb over the margin, six brand-name combination drugs |
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

Run one image only: `python run.py --local rx8`.

Each result is saved to `results/<local|featherless>/<image>.json`: the raw model output, the parsed JSON, the
time taken and the token counts. `results/` is git-ignored in this repo; to push the results back, run
`git add -f results && git commit -m "parrotlet results" && git push`.

## What a human read on each page (to compare against)

`~` = likely reading, `?` = unclear to the human reader too.

**rx1**: BP 100/80 · FBS 146 · 2h PPBS 342 · K/c/o T2DM (4 y), non-smoker, DSPN
1. Diabetic diet
2. Regular exercise, 30 min a day
3. Inj. Insugen (30/70): 18 units before breakfast → 4 units before dinner ~, 30 min before food
4. Tab Doloneurom-NT (200/10) ?: ½ tab after dinner × 6 days, then 1 tab after dinner × 1 month
5. Cap Myelobest ~: 1 after dinner

Advised: USG abdomen & pelvis (pancreas morphology), Sr. creatinine, fasting lipid profile, FBS, 2h PPBS

**rx3**: Date 3/10/26 · Sex M · BP 110/82 · FBS 180 · PPBS 246 mg/dl · K/c/o T2DM ~ · "Reluctant for insulin"
1. Tab Glimisave MV 2.2 ~: 1 before breakfast
2. Tab Cospiaq SM 25/1000 ?: 1 before breakfast ~
3. Tab Geminor M4 ?: 1 before meal ?
4. Tab Rosuhelp 10 ~: 1 at night ~
5. Tab Myelohelp ~: 1 after … ?
6. Cap PAN-D: 1 before breakfast × 10 days ~

Advised: FBS, 2h PPBS after 1 month

**rx8**: Date 4/10/26 · BP 116/81 · C/O calf pain (both sides) since 6 days
1. Tab Etoshine-MR: 1 BD after food × 10 days
2. Tab Myelohelp: 1 OD after food × 30 days
3. Tab Uprise-D3: 1 once weekly for 3 months
4. Cap Susrab-DSR: 1 OD before food × 10 days
5. Flenabenz ? Gel: local application BD

The human readings are not verified ground truth either; disagreements are worth checking against the image.
