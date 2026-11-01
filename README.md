# markpipe

Read the text that someone circled with a pen on a scanned page.

```
marked page ─┐
             ├─ detect ── one box per pen mark ── inside crop ── reader ── text
clean page ──┘   (pixel diff, no model)          (only what the     (PaddleOCR-VL, Qwen, any VLM,
                                                  circle encloses)   OCR engine, any API)
```

1. **Detect.** Subtract the clean page from the marked page. Every pixel that changed is pen ink, whatever its
   colour. Group the ink into marks and classify each one:
   - closed circle; small breaks in the stroke are bridged
   - open stroke: a tick, an underline, or a circle with a large part missing
   - a circle drawn over twice, kept as one mark
   - two touching circles, split in two
2. **Crop.** For every closed mark, cut its window from the clean page and whiten everything outside the circle's
   interior. The crop holds only the circled text: no ink, no neighbouring lines.
3. **Read.** Send each crop to a reader and save its answers.

## Layout

```
markpipe/                     the package
├── config.py                 DetectorConfig: every threshold, validated
├── detect.py                 ink mask, grouping, gap bridging, double-loop / touching-circle handling
├── crops.py                  inside crop, overlay and ink-only review images
├── dataset.py                finds <page>_marked / <page>_unmarked pairs in a folder
├── pipeline.py               detect_pages() and read_crops(), the two stages
├── cli.py                    python -m markpipe ...
└── readers/
    ├── base.py               Reader interface, answer clean-up
    ├── mlx_vlm.py            any mlx-vlm model (PaddleOCR-VL, Qwen3.5, Gemma 4, ...)
    ├── openai_compat.py      any OpenAI-compatible server (Ollama, vLLM, LM Studio, llama.cpp, OpenRouter)
    ├── ocr_engines.py        RapidOCR (PP-OCR), Tesseract
    └── __init__.py           presets and create_reader("spec")
experiment/
├── dataset/                  raw/ (20 pages, img_NN.png) and ready_to_use/ (7 pairs, img_NN_marked / _unmarked)
├── dataset.zip               the same folder, zipped
├── answer_key.json           expected circled text for the 7 pages (38 items)
├── score.py                  found / exact / extras per page
└── run_experiment.py         detect + read with several readers + score, one model in memory at a time
tests/                        edge cases, input errors, reader selection, both stages with a stand-in reader
```

## Setup

```bash
pip install -r requirements.txt     # or: pip install -e ".[mlx,ocr,test]"
```

- **MLX readers** need Apple Silicon.
- **Tesseract** is a system program: `brew install tesseract`.
- **`openai:` readers** need nothing extra.

## Usage

```bash
python -m markpipe readers                                                   # list reader presets
python -m markpipe detect --data experiment/dataset/ready_to_use --out out    # boxes + crops, no model
python -m markpipe read   --out out --reader paddleocr-vl
python -m markpipe run    --data experiment/dataset/ready_to_use --out out --reader tesseract
```

Each page gets `out/<page>/`, containing:
- `overlay.png`: the marks outlined on the page
- `ink_only.png`
- `crops/marker_NN.png`
- `markers.json`: boxes, shape, ink colour, notes

Answers go to `out/reads/<reader>.json`.

Readers:

| spec | what it runs |
|---|---|
| `paddleocr-vl` | PaddleOCR-VL 1.5, bf16, via mlx-vlm. OCR model: always sent its own `OCR:` prompt |
| `qwen3.5-4b`, `qwen3.5-9b`, `qwen3-vl-2b`, `gemma4-e2b`, `glm-ocr`, ... | other MLX presets (`python -m markpipe readers`) |
| `mlx:<huggingface repo>` | any mlx-vlm model, e.g. `mlx:mlx-community/SmolVLM2-2.2B-Instruct-mlx` |
| `openai:<model>` | any OpenAI-compatible server: `--base-url http://localhost:11434/v1` (Ollama), `:8000/v1` (vLLM) |
| `rapidocr`, `tesseract` | classic OCR on CPU |

Options:
- `--task-prompt "OCR:"` makes any model an OCR-style reader.
- `--thinking on|off` controls reasoning models.
- `--max-tokens` limits the answer length.
- `--api-key-env NAME` names the environment variable holding a hosted API's key.

From Python:

```python
from markpipe import DetectorConfig, create_reader, detect_pages, find_pairs, read_crops

detect_pages(find_pairs("experiment/dataset/ready_to_use"), "out", DetectorConfig(gap=8))
with create_reader("paddleocr-vl") as reader:
    rows = read_crops("out", reader)   # [{"page", "id", "answer", "seconds", "error"}, ...]
```

To add a reader, subclass `markpipe.Reader` and implement `read(image, prompt) -> str`.

## Experiment

```bash
python experiment/run_experiment.py --readers paddleocr-vl,tesseract,rapidocr
python -m pytest
```

Results on the 7 pages (38 circled items), on an 8 GB M2:

- **Detection:** 38/38 marks, all closed.
- **Reading:**

| reader | found | exact | extras | s/crop |
|---|---|---|---|---|
| PaddleOCR-VL 1.5 bf16 | **38/38** | **38/38** | 0 | 0.5 |
| Tesseract 5 | 34/38 | 33/38 | 2 | 0.07 |
| RapidOCR (default PP-OCR models) | 33/38 | 33/38 | 5 | 0.23 |

- **found:** the expected text appears as whole words in the answer.
- **exact:** the answer is exactly the expected text, ignoring case and punctuation.
- **extras:** answers that match nothing.
- **The OCR engines' misses** are misreads of small print, e.g. "Buston" for "Boston", "yo" for "NO", "unobtruaive".

## Limitations

- **Detection needs the clean page.** The diff in `ink_mask()` needs the unmarked original of each page. To work
  from a marked scan alone, replace `ink_mask()` with a colour- or model-based mask and keep everything after it.
- **Test set size.** 38 items on 7 low-resolution (~90 dpi) pages is too few to separate readers that are within one
  or two items of each other.
