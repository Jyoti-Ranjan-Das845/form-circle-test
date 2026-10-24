# form-circle-test

A small benchmark for one question: **can a pipeline tell what a person circled on a scanned page?**

It has 20 real scanned pages (from the public RVL-CDIP collection), a hand-marked copy of each, an answer key,
and an evaluator you can point at any pipeline: OCR + rules, OCR + LLM, a vision model, or anything else.

## Quick start

```bash
uv venv .venv && uv pip install -r requirements.txt     # or: python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m formeval.run --pipeline pipelines/oracle.py   # sanity check: must print ACCURACY 100%
.venv/bin/python -m formeval.run --pipeline pipelines/empty.py    # floor: finds nothing
```

Run your own pipeline:

```bash
.venv/bin/python -m formeval.run --pipeline pipelines/my_pipeline.py            # every marked page
.venv/bin/python -m formeval.run --pipeline pipelines/my_pipeline.py --gray     # same pages in grey, so red ink can't be a shortcut
.venv/bin/python -m formeval.run --pipeline pipelines/my_pipeline.py:extract --pages 01,02,20
```

Only pages whose copy in `real_forms_marked/` differs from the clean original are graded, so you can run it while
marking is still in progress.

## Writing a pipeline

Copy `pipelines/template.py`. A pipeline is one function, `run(task) -> dict`, called once per page.
The full contract is in [`formeval/contract.py`](formeval/contract.py).

**Input** (`task`):

| key | value |
|---|---|
| `page_id` | `"01"` … `"20"` |
| `image_path` | path to the marked page image |
| `kind` | `"text"` (pages 01–10) or `"options"` (pages 11–20) |
| `instruction` | plain-English description of the expected output (usable as an LLM prompt) |
| `schema` | options pages only: the questions and their allowed options (`data/schemas/NN.json`) |

**Output, text pages** — every circled piece of printed text, plus the line it sits on:

```json
{"marked": [{"text": "smoking", "context": "the period when smoking was banned on"}]}
```

**Output, options pages** — one answer per question id, using the schema's option labels (or codes):

```json
{"answers": {"q1": "YES", "q1_2_3": null, "q1_3": "Sometimes worse, sometimes better", "q2": ["Coffee", "Mouth wash"]}}
```

The pipeline never sees the answer key (`data/ground_truth/`).

## Scoring

One number: **accuracy = correct ÷ (items in the answer key + extra things the pipeline reported)**.

- **Text pages:** each circled word counts once. Reporting text that was not circled adds an error.
  For words that appear more than once on a page, `context` must point at the right line.
- **Options pages:** each question counts once. `null` is correct when the question was left blank and wrong
  when something was circled. Multi-select answers must match exactly.
- Matching ignores case, extra spaces and punctuation at the ends (`"Pittsburgh,"` = `"Pittsburgh"`),
  treats every dash the same (`"−3.92"` = `"-3.92"`) and accepts an option's printed code in place of its label.

Each run prints per-page scores with every miss and extra, and saves the predictions and a `report.json`
under `results/<pipeline>/<timestamp>-<color|gray>/`.

## Layout

```
real_forms/            20 clean scanned pages (01–10 dense text, 11–20 questionnaires)
real_forms_marked/     the same pages with red hand-drawn circles — mark these
data/schemas/          questions + options for pages 11–20 (given to pipelines)
data/ground_truth/     answer key for every page, with where/how each item was marked (grader only)
marking_plan.md        what to circle on each page — generated: python tools/make_marking_plan.py
formeval/              contract, text normalisation, grader, runner
pipelines/             template.py, oracle.py (reads the key; must score 100%), empty.py
tests/                 grader tests: python -m unittest discover tests
tools/                 fetch_rvl.py (pulls candidate pages), synthetic/ (generator for synthetic forms)
```

Editing the answer key: change `data/ground_truth/NN.json`, then rerun `python tools/make_marking_plan.py`
and the tests.

Source images: RVL-CDIP via `huggingface.co/datasets/jordyvl/rvl_cdip_100_examples_per_class`
(scanned documents from the UCSF Industry Documents Library).
