# markpipe: find pen-circled text on scanned pages

A rewrite of `experiments/marker_crops` as a small package. The pipeline is unchanged: same algorithm, same
defaults, same 38 boxes. It is split into modules, and the reading step is pluggable.

```
marked page ─┐
             ├─ detect ── one box per pen mark ── crop ── read ── text
clean page ──┘   (pixel diff, no model)          (marked / inside)   (PaddleOCR-VL, Qwen, any VLM, OCR)
```

1. **Detect.** Subtract the clean page from the marked page. Every pixel that changed is ink, whatever its colour.
   Group the ink into marks and classify each one:
   - closed circle; small breaks in the stroke are bridged
   - open stroke: a tick, an underline, or a circle with a large part missing
   - a circle drawn over twice, kept as one mark
   - two touching circles, split in two
2. **Crop.** Cut each mark's window out of the page, in up to three versions:
   - `marked`: from the marked page, with the ink
   - `clean`: the same window from the clean page
   - `inside`: only the circle's interior from the clean page, everything else whitened
3. **Read.** Send the crops to a reader and save its answers.

## Layout

```
marker_pipeline/
├── markpipe/                 the package
│   ├── config.py             DetectorConfig: every threshold, with validated defaults
│   ├── detect.py             ink mask, grouping, gap bridging, double-loop / touching-circle handling
│   ├── crops.py              marked / clean / inside crops, overlay and ink-only images
│   ├── dataset.py            finds <page>_marked / <page>_unmarked pairs in a folder
│   ├── pipeline.py           detect_pages() and read_crops(), the two stages
│   ├── cli.py                python -m markpipe ...
│   └── readers/
│       ├── base.py           Reader interface, answer clean-up
│       ├── mlx_vlm.py        any mlx-vlm model (PaddleOCR-VL, Qwen3.5, Gemma 4, ...)
│       ├── openai_compat.py  any OpenAI-compatible server (Ollama, vLLM, LM Studio, llama.cpp, OpenRouter)
│       ├── ocr_engines.py    RapidOCR (PP-OCR), Tesseract
│       └── __init__.py       presets and create_reader("spec")
├── experiment/
│   ├── dataset/              raw/ (20 pages, img_NN.png) and ready_to_use/ (7 pairs, img_NN_marked / _unmarked)
│   ├── dataset.zip           the same folder, zipped
│   ├── answer_key.json       expected circled text for the 7 pages (38 items)
│   ├── score.py              found / exact / extras per page
│   └── run_experiment.py     detect + read with several readers + score, one model in memory at a time
└── tests/                    edge cases, input errors, reader selection, both stages with a stand-in reader
```

## Setup

```bash
pip install -r requirements.txt     # or: pip install -e ".[mlx,ocr,test]"
```

On this repo's Mac the existing environment works: `../.venv_vlm/bin/python` (it has mlx-vlm and RapidOCR).

## Usage

Run from the `marker_pipeline/` folder.

```bash
python -m markpipe readers                                                   # list reader presets
python -m markpipe detect --data experiment/dataset/ready_to_use --out out    # boxes + crops, no model
python -m markpipe read   --out out --reader paddleocr-vl --modes marked,inside
python -m markpipe run    --data experiment/dataset/ready_to_use --out out --reader qwen3.5-4b
```

Readers:

| spec | what it runs |
|---|---|
| `paddleocr-vl` | PaddleOCR-VL 1.5, bf16, via mlx-vlm. OCR model: always sent its own `OCR:` prompt |
| `qwen3.5-4b`, `qwen3.5-9b`, `qwen3-vl-2b`, `gemma4-e2b`, `glm-ocr`, ... | other MLX presets (`python -m markpipe readers`) |
| `mlx:<huggingface repo>` | any mlx-vlm model, e.g. `mlx:mlx-community/SmolVLM2-2.2B-Instruct-mlx` |
| `openai:<model>` | any OpenAI-compatible server: `--base-url http://localhost:11434/v1` (Ollama), `:8000/v1` (vLLM) |
| `rapidocr`, `tesseract` | classic OCR on CPU |

- **Options:**
  - `--task-prompt "OCR:"` makes any model an OCR-style reader.
  - `--thinking on|off` controls reasoning models.
  - `--max-tokens` limits the answer length.
  - `--api-key-env NAME` names the environment variable holding a hosted API's key.
- **Modes:**
  - `marked` is the realistic one: the reader has to find the circle in the crop.
  - `inside` gives only the circled text.
  - `clean` is the window without ink.
  - `both` sends the marked and clean crops together, for multi-image models.

From Python:

```python
from markpipe import DetectorConfig, create_reader, detect_pages, find_pairs, read_crops

pages = detect_pages(find_pairs("experiment/dataset/ready_to_use"), "out", DetectorConfig(gap=8))
with create_reader("paddleocr-vl") as reader:
    answers = read_crops("out", reader, modes=["marked", "inside"])
```

Adding a reader means subclassing `markpipe.Reader` and implementing `read(images, prompt) -> str`.

## Experiment

```bash
python experiment/run_experiment.py --readers paddleocr-vl,rapidocr,tesseract --modes marked,inside
python -m pytest
```

Results on the 7 pages (38 circled items), 2026-11-02, on an 8 GB M2:

- **Detection:** 38/38 marks, all closed, identical boxes and crops to `experiments/marker_crops`.
- **Reading:**

| reader | crops | found | exact | extras | s/crop |
|---|---|---|---|---|---|
| PaddleOCR-VL 1.5 bf16 | inside | **38/38** | **38/38** | 0 | 0.52 |
| PaddleOCR-VL 1.5 bf16 | marked | 36/38 | 28/38 | 2 | 0.56 |
| Qwen3.5-4B 6-bit, thinking off | marked | **38/38** | **38/38** | 0 | 3.09 |
| Tesseract 5 | inside | 34/38 | 33/38 | 2 | 0.06 |
| Tesseract 5 | marked | 17/38 | 0/38 | 15 | 0.09 |
| RapidOCR (default PP-OCR models) | inside | 33/38 | 33/38 | 5 | 0.21 |
| RapidOCR (default PP-OCR models) | marked | 27/38 | 10/38 | 10 | 0.24 |

- **Scoring:**
  - **found:** the expected text appears as whole words in the answer.
  - **exact:** the answer is exactly the expected text, ignoring case and punctuation.
  - **extras:** answers that match nothing.

  This is stricter than `experiments/marker_crops/score_crops.py`, which counted plain substrings, so "SNOT" counted for "NOT" and "23" for "3". Rescored this way, the earlier saved Qwen3.5-9B answers are 38/38 on both marked and inside crops.
- **Why OCR engines lose on marked crops:** they take no instruction, so they transcribe the whole window, including slivers of neighbouring lines and the ink. Their fair test is the inside crop.

## Limitations

- **Detection needs the clean page.** The diff in `ink_mask()` needs the unmarked original of each page, which a
  real scan doesn't have. To work from the marked page alone, replace `ink_mask()` with a colour- or
  model-based mask and keep everything after it.
- **Answer key size.** The answer key has 38 items on 7 low-resolution (~90 dpi) pages, which is too few to separate
  readers that are within one or two items of each other.
