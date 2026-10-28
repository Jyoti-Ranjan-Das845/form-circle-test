# Pipeline plan: finding hand-circled text, fast and open source

Goal: given a scanned page, return **the printed text inside every hand-drawn circle** (text pages) or **the
circled option per question** (form pages, with the schema). Judged on two things: **accuracy** (our evaluator)
and **latency** (seconds per page on the M2 / 8 GB Mac). Everything must be open source, small, and generic:
no colour shortcuts, no tuning on the 20 test pages.

## 1. What we already know (measured)

| Tried | Accuracy | Latency | Lesson |
|---|---|---|---|
| PaddleOCR-VL-1.6 parsing (page 04) | read all 6 circled words, but **never flagged a circle** | ~100 s/page | a top parser is a reader, it ignores marks |
| Qwen3-VL-2B, whole page, one prompt (7 pages) | **16.7 %** colour, **11.9 %** grey | ~5 s/page | page shrunk to ~800 image tokens: the pen line is invisible; hits were guesses |

So a pipeline is only worth trying if some part of it **actually looks at the marks at a usable resolution**.

## 2. Ruled out (cannot work, or breaks the constraints)

| Type | Why not |
|---|---|
| OCR → text-only LLM | the circle is gone once the page is text |
| OCR parser alone (PaddleOCR-VL, MinerU, olmOCR…) | trained to transcribe; shown above to ignore circles |
| Whole page → small VLM | shown above (≤17 %) |
| Large VLMs (> 4B), cloud APIs | too heavy for the laptop / not open source |
| Template OMR software (ABBYY-style) | needs a hand-made template per form; not generic |
| Fine-tuned layout models (LayoutLMv3, Donut) | need labelled real examples per form type |
| Training a custom mark detector (e.g. YOLO26n) | dropped by choice: no training in this study |
| OCR + handwriting-vs-print pixel separator | no ready open model exists; would need training |
| Subtract a blank copy of the form | needs a blank copy of every form; not generic |
| OCR + open-vocabulary *box* detector (Grounding DINO, YOLOE, Florence-2) | same type as P2; SAM 3 chosen as the strongest of that family |
| Cascades (e.g. P1, then P4 only when unsure) | combinations of the types below; worth trying after the single types are measured |

## 3. Shared parts (same in every pipeline, so the comparison is fair)

- **OCR: PP-OCRv6 (PaddleOCR 3.x general OCR pipeline, `return_word_box=True`)**: line *and word* boxes.
  Evidence: PP-OCRv6_medium beats PP-OCRv5_server by +5.1 recognition / +4.6 detection, the tiny tier is
  3.9× faster than PP-OCRv5_mobile on CPU, 1.5M–34.5M parameters ([paper](https://arxiv.org/abs/2606.13108)).
  Word boxes are an opt-in output of the pipeline ([docs](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/OCR.html)).
  Runs on CPU; no VLM, no GPU needed.
- **Mapper (plain Python)**: turns "this region is circled" into the contract answer.
  - text pages: the OCR words mostly inside the circle, in reading order, plus their OCR line as `context`.
  - form pages: for each schema question, find its option labels/codes in the OCR words near the question
    text, and pick the option(s) inside a circle; `null` if none.
- **Practice set (for tuning P1's rules only, nothing is trained)**: random hand-drawn-style circles rendered on the ~780 unused
  RVL-CDIP pages in many styles (black/blue/pencil/red, thin/thick, open/tight/loose/double), with exact answers.
  The 20 test pages are never used for tuning.
- **Evaluator ink versions**: besides colour and grey, repaint the marks as **black pen, blue pen and pencil**
  (we know the exact mark pixels: marked minus clean). Main score = black ink, the hardest and most realistic.

## 4. Pipeline types and one candidate each

No pipeline trains anything; every model is used as released.

| # | Type | Components, in order | Expected latency* |
|---|---|---|---|
| P1 | OCR + classical CV | OCR model (PP-OCRv6) → OpenCV mark rules → mapper | **~1 s** |
| P2 | OCR + vision foundation model | OCR model (PP-OCRv6) → promptable segmentation model (SAM 3) → mapper | ~5–15 s |
| P3 | OCR + VLM (Set-of-Mark) | OCR model (PP-OCRv6) → numbered boxes drawn on the image → VLM (Qwen3-VL-2B) → mapper | ~5–8 s |
| P4 | OCR + classical CV + VLM (propose, then verify on crops) | OCR model (PP-OCRv6) → OpenCV mark rules → crop + enlarge → VLM (Qwen3-VL-2B) → mapper | ~10–20 s |
| P5 | Document parsing toolkit + VLM (instruction-driven) | Marker (its own layout + OCR models) → local VLM via Ollama | slow (≥30 s) |
| P6 | VLM only, tiled | page cut into overlapping tiles → VLM (Qwen3-VL-2B) per tile: "list the circled text" → merge | ~15–25 s |
| P7 | VLM locates (tiled) + OCR reads | page cut into tiles → VLM (Qwen3-VL-2B) per tile: "boxes of hand-drawn circles" → OCR model (PP-OCRv6) → mapper | ~15–25 s |

\*Estimates to be measured, not results.

Each type passes the same test: some component **looks at the marks at a usable resolution** (pixel rules,
a segmentation model, or a VLM on a sharp enough image) **and** some component reads the printed text.

A VLM (vision-language model) takes an image plus text and *writes text*. SAM 3 is a vision foundation model
for segmentation: it takes an image plus a short phrase and returns *masks*, never text.

### P1: OCR + classical CV (no model for the marks)
- **How:** binarise the page → erase the pixels inside OCR word boxes (slightly shrunk) → what remains is
  non-text ink → group into strokes → keep strokes that are long, thin, curved and enclose or cut across word
  boxes → circled words = words enclosed by a stroke's filled outline.
- **Why this candidate:** the classic approach for exactly this problem (user-drawn circle extraction from
  scans, [US6597808](https://patents.google.com/patent/US6597808); print/annotation separation by morphology,
  [Xerox](https://patents.google.com/patent/US6904170)). Free and near-instant.
- **Risks:** circles cutting through letters, open circles, table lines and old handwriting on the page.

### P2: OCR + vision foundation model (SAM 3)
- **How:** SAM 3 with the text prompt "hand-drawn circle" (never "red") → one mask per circle → fill the loop →
  words inside = circled.
- **Why this candidate:** SAM 3 is the current open state of the art for text-prompted segmentation of *any*
  concept (270K-concept benchmark, about 2× earlier systems; [paper](https://arxiv.org/html/2511.16719v1),
  [code](https://github.com/facebookresearch/sam3)). A native **MLX port** runs on Apple Silicon with text
  prompts (0.8B, ~3.4 GB, Apache-2.0; [mlx-community/sam3-image](https://huggingface.co/mlx-community/sam3-image)).
  Masks beat boxes here: they show which words the loop actually encloses.
- **Considered instead:** YOLOE-26 (much faster, real-time open-vocabulary, but its LVIS accuracy is far lower;
  [docs](https://docs.ultralytics.com/models/yolo26/)), Grounding DINO, OWLv2, Florence-2 (boxes only,
  [comparison](https://www.forasoft.com/learn/ai-for-video-engineering/articles-ai/open-vocabulary-detection-grounding-dino-florence-2-rtdetr-rfdetr)).
- **Risks:** pen loops on paper are far from its training data; ~3.4 GB in 8 GB RAM; speed on M2 not published.

### P3: OCR + VLM (Set-of-Mark prompting)
- **How:** draw small numbered boxes on the page for each OCR line/word (Set-of-Mark), send the image plus the
  numbered list to the VLM, ask only **"which numbers are circled?"** (text pages) or the schema questions with
  option ids (form pages). The VLM writes a few numbers; the text comes from OCR, so no spelling errors.
- **Why this candidate:** Set-of-Mark prompting is the standard way to make a VLM ground answers in image regions
  ([Yang et al. 2023](https://arxiv.org/abs/2310.11441)). Qwen3-VL-2B is the smallest current model with free
  prompts and grounding that runs locally on MLX (already installed and measured at ~4 s/call;
  [repo](https://github.com/qwenlm/qwen3-vl)). InternVL3.5-1B/2B is the closest alternative
  (RefCOCO 81.4 at 1B; [paper](https://arxiv.org/html/2508.18265v1)).
- **Risks:** still whole-page resolution, so faint or small circles may stay invisible.

### P4: OCR + classical CV + VLM (mark proposals → VLM reads crops)
- **How:** take P1's candidate marks with a loose (high-recall) setting → crop each with a margin, upscale →
  ask the VLM per crop: "Is printed text circled by hand here? If yes, return exactly that text, else NONE." →
  snap the answer to OCR words in the crop.
- **Why this candidate:** fixes the resolution problem directly: in a crop the pen line is big and clear. Cheap
  proposals keep the number of VLM calls small (one per candidate mark, not per line).
- **Risks:** latency grows with the number of proposals; if P1 misses a mark, P4 misses it too.

### P5: Document parsing toolkit + VLM (Marker)
- **How:** Marker converts the page; with `--use_llm` and a custom `block_correction_prompt` ("mark which text is
  circled by hand"), its LLM step sees page images plus the parsed blocks
  ([v1.8 notes](https://newreleases.io/project/github/datalab-to/marker/release/v1.8.0),
  [prompt docs](https://documentation.datalab.to/docs/labs/marker-prompt-api/overview)). Local VLM via Ollama.
- **Why this candidate:** the only maintained open-source parser where you change behaviour with an instruction
  instead of code.
- **Risks:** heaviest on 8 GB (layout + OCR + VLM models together), slowest, and Marker's model weights have a
  restricted licence for commercial use. Run last.

### P6: VLM only, tiled
- **How:** cut the page into 4–6 overlapping tiles, enlarge each, ask the VLM per tile for the circled text
  (or the schema answers it can see), merge and drop duplicates from the overlaps. No OCR.
- **Why it can work:** the whole-page run failed because the page was shrunk; a tile gives the VLM several times
  more pixels per pen line, the same fix as P4 but without needing anything to propose the spots.
- **Risks:** a circle cut by a tile edge (handled by overlap), more calls per page, and the VLM's own reading of
  small print may be wrong (no OCR to correct it).

### P7: VLM locates (tiled) + OCR reads
- **How:** same tiles as P6, but the VLM only returns **boxes** of hand-drawn circles (its grounding mode);
  boxes are mapped back to page coordinates, and OCR words inside each box are the answer.
- **Why it can work:** the VLM does the looking, OCR does the reading; the reverse split of P3 and P4.
- **Risks:** small-VLM boxes can be loose or misplaced (the full-page grounding run missed every circle).

## 5. Order of work

1. Shared parts: PP-OCRv6 install, mapper, ink versions in the evaluator, practice-set generator.
2. P1 (baseline, also provides proposals for P4).
3. P3, P4, P6, P7 (all reuse the installed Qwen3-VL-2B).
4. P2 (needs the 3.4 GB SAM 3 download).
5. P5 if time and memory allow.

Each pipeline is one file in `pipelines/` following the contract; every run reports accuracy (colour, grey,
black ink) and seconds per page on the same 7+ marked pages.
