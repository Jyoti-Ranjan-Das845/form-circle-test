# Results: finding hand-circled text, 7 marked pages

## Leaderboard (all models, original red marks)

38 circles: 33 on the text pages 01–06 and 5 on the YES/NO form (page 20; its sixth question has nothing circled).
**Found** = circles reported correctly, ignoring which occurrence of a repeated word was meant. **Extras** = items
reported that are not circled, plus an answer given for the blank question. Original colour pages, no preprocessing.
Recomputed with `tools/failure_analysis.py` (OCRia-1 with `experiments/opendocrouter/score.py`).

| # | Model / pipeline | Where it runs | Found / 38 | Extras | s/page |
|---|---|---|---|---|---|
| 1 | **GPT-6 Luna**, medium reasoning, direct prompt | OpenRouter API | **38** | **0** | 7 |
| 2 | Gemma 4 26B-A4B, direct prompt | OpenRouter API | 32 | 12 | 5 |
| 3 | Qwen3-VL-2B bf16, P6 (6 zoomed tiles) | local, 8 GB Mac | 29 | 26 | 78 |
| 4 | OCRia-1, every underline / highlight / strikethrough counted | OpenDocRouter API | 27 | 39 | 4 |
| 5 | Qwen3.5-4B 6-bit, thinking on (8,000 tokens) | local | 23 | 5 | 55 |
| 6 | Qwen3.5-4B 6-bit, thinking off | local | 18 | 9 | 15 |
| 7 | Gemma 4 E2B 6-bit, thinking on, image only | local | 16 | 3 | 21 |
| 7 | Gemma 4 E2B 6-bit, thinking on, image + OCR text | local | 16 | 5 | 28 |
| 7 | Qwen3-VL-2B bf16, whole page | local | 16 | 66 | 11 |
| 10 | Florence-2-large bf16, P7 (detection on tiles + OCR) | local | 15 | 4 | 13 |
| 10 | Qwen3-VL-2B Instruct 4-bit (Ollama, by hand) | local | 15 | 14 | 6–9 |
| 12 | Mistral Small 2603, direct prompt | OpenRouter API | 9 | 9 | 35 |
| 13 | Moondream 3.1, direct prompt | OpenRouter API | 7 | 15 | 5 |
| 14 | OCRia-1, only its explicit "(circled)" note | OpenDocRouter API | 5 | 0 | 4 |
| 15 | Gemma 3 4B, direct prompt | OpenRouter API | 3 | 36 | 6 |
| 16 | Docling + NuExtract-2B extraction (text pages only, out of 33) | local | 1 | – | 120–420 |

Direct prompt (text pages): "Can you identify which words are circled in red in the image? Reply with a JSON list of
the words." Page 20: "The right answer to each question is marked with a red circle. If nothing is circled for a
question, the answer is null. Reply with all the answers you can see in the image, as JSON {"<question id>":
"<answer>"}." plus the question list. The Ollama row is from `docs/manual_ollama_tests.md` (raw replies in
`experiments/ollama/`); the Docling row from `docs/docling_test_plan.md`.

## First round: local pipelines (accuracy)

Pages 01–06 (dense text) and 20 (YES/NO form), 39 graded items. Score = correct ÷ (items + extra things reported).
**Black** = the marks repainted as black pen on the clean page (main, realistic score); **colour** = the original
red marks. Latency = median seconds per page on an M2 MacBook (8 GB), one model loaded at a time; the first page
of each run also includes model loading. All models are open source and run locally; nothing was trained.

| # | Pipeline | Model | Black | Colour | s/page |
|---|---|---|---|---|---|
| ceiling | OCR + mapper given the **true** circle positions (cheats) | – | 69.8 % | – | 2 |
| – | Whole page → VLM, one prompt | Qwen3-VL-2B | – | 16.7 % (grey 11.9 %) | 5 |
| P1 | OCR + classical CV | – | 22.2 % | 4.7 % | **4** |
| P2 | OCR + vision foundation model | SAM 3 | 24.5 % | 2.6 % | 48 |
| P3 | OCR + VLM, numbered lines (Set-of-Mark) | Qwen3-VL-2B | 5.0 % | 7.3 % | 13–16 |
| P3 | 〃 | SmolVLM2-2.2B | 2.5 % | 2.4 % | 53–57 |
| P4 | OCR + CV proposals + VLM on crops | Qwen3-VL-2B | 21.3 % | 7.0 % | 9–13 |
| P4 | 〃 | SmolVLM2-2.2B | 11.9 % | 2.5 % | 39–84 |
| P4 | 〃, judged by caption (`<DETAILED_CAPTION>`) | Florence-2-large | 2.6 % | 2.6 % | 15–28 |
| **P6** | **VLM only, tiled (6 tiles)** | **Qwen3-VL-2B** | **36.7 %** | **44.8 %** | 34–36 |
| P6 | 〃 | SmolVLM2-2.2B | 4.8 % | – | 211 |
| P7 | VLM boxes on tiles + OCR reads | Qwen3-VL-2B | 10.9 % | 15.1 % | 34–37 |
| P7 | 〃, `<OPEN_VOCABULARY_DETECTION>` | Florence-2-large | 8.2 % | 37.2 % | 18–19 |
| P7 | 〃 | SmolVLM2-2.2B | 2.6 % | – | 200 |
| P5 | Parsing toolkit + VLM (Marker) | – | skipped: needs several models in memory at once | | |

## What it says

1. **Best accuracy: P6, Qwen3-VL-2B on 6 zoomed tiles**: 36.7 % black / 44.8 % colour, about half the ceiling,
   at ~35 s/page. Zooming is what helps: the same model on the whole page scored 12–17 %.
2. **Fastest: P1 (no model for marks), ~4 s/page**, 22 % on black ink, but it treats thin red pen as paper (4.7 %).
3. **SAM 3 locates black-ink circles** (found all 6 on page 04) but is slow (~48 s/page) and almost blind to the
   thin red lines; its text then suffers from OCR noise around the strokes.
4. **Colour shortcut:** Florence-2 detection scores 37 % on red marks but 8 % on black; the black-ink score exposes it.
5. **SmolVLM2-2.2B** is slower than Qwen on 8 GB (GPU timeouts and out-of-memory errors) and much less accurate.
6. **Florence-2 captions never mention the circle**, so the caption route cannot detect marks.
7. **The ceiling is 70 %**: even with perfect circle positions, OCR misreads degraded scans; the best pipeline
   reaches half of that.

## Rerun with uncompressed models (bf16), original colour pages

Same pipelines and pages, original red marks, models at their released precision instead of 4-bit / 8-bit.
"Found" = circled items returned, counted even if a repeated word is reported without its line.

| Pipeline | Qwen3-VL-2B 4-bit | **Qwen3-VL-2B bf16** | s/page 4-bit → bf16 |
|---|---|---|---|
| Direct prompt, no OCR* | 25.0 % (13 found) | 13.2 % (16 found, 66 wrong extras) | 6 → 11 |
| P3 OCR + numbered lines | 7.3 % (3 found) | 12.2 % (6 found) | 16 → 43 |
| P4 OCR + CV + crops | 7.0 % (3 found) | 7.3 % (3 found) | 9 → 31 |
| **P6 zoomed tiles** | 44.8 % (26 found) | **45.3 % (29 found)** | 34 → 78 |
| P7 tiles + boxes + OCR | 15.1 % (8 found) | 16.7 % (8 found) | 37 → 150 |

| Pipeline | Florence-2-large 8-bit | **Florence-2-large bf16** | s/page |
|---|---|---|---|
| P4 crops judged by `<DETAILED_CAPTION>` | 2.6 % | 2.6 % | 15 → 12 |
| P7 `<OPEN_VOCABULARY_DETECTION>` on tiles + OCR | 37.2 % | 37.2 % | 19 → 13 |

\*The two direct runs also differ in prompt: the bf16 run used the corrected prompt "Can you identify which words
are circled in red in the image?", which asks for *words*, so the model split phrases and listed many extra words.

What changed: removing compression gives Qwen a little more recall (it finds a few more circled items in every
pipeline) but it is 2–4× slower on the 8 GB Mac and, with the direct prompt, lists far more uncircled words.
Florence-2 behaves the same at 8-bit and bf16. The ranking does not change: zoomed tiles with Qwen remain best
(45 %), Florence-2 detection second on red marks (37 %).

## Qwen3.5-4B, direct prompt (Oct 27)

`mlx-community/Qwen3.5-4B-6bit` (bf16 9.1 GB and 8-bit 5.1 GB run out of GPU memory on the 8 GB Mac), same two
prompts as the other direct runs, colour pages, found / 38 with position ignored. `pipelines/direct_vlm.py:run_qwen35`
(thinking off, 200/300 answer tokens) and `:run_qwen35_think` (thinking on, 4,000 tokens). Raw replies, including the
reasoning, are saved in each prediction; `tools/reparse.py` re-scores them.

| Page | Thinking off | Thinking on |
|---|---|---|
| 01 | 2/4 | 0/4 (reasoning used all 4,000 tokens, no answer) |
| 02 | **5/5** | 3/5 |
| 03 | 0/6 (looped on "regularly") | 3/6 |
| 04 | 1/6 (split the heading, looped on "inhalation") | 0/6 (no answer) |
| 05 | **5/5** | 4/5 |
| 06 | 1/7 (looped) | 5/7 |
| 20 | 4/5 | **5/5** |
| **Total** | **18/38**, 15 s/page | **20/38**, 21–280 s/page |

Re-run of pages 01 and 04 with an 8,000-token thinking budget (`results/qwen35_think8k/`): page 01 finished after
365 s with **3/4** (smoking, Germantown, unobtrusive; it also claimed "smoking" was circled in five places and added
"alarm"); page 04 again used the whole budget (541 s) going back and forth on whether the circle covers "inhal" or
"inhale", so **0/6**. With 8,000 tokens the thinking total is **23/38**.

Qwen3.5 sometimes answers with `{"bbox_2d": [...], "text_content": "..."}` objects; the parser now reads those.

## GPT-6 Luna via OpenRouter (Oct 28)

`openai/gpt-6-luna`, medium reasoning effort, same two prompts, original colour pages
(`pipelines/openrouter_gemma.py:run_luna`, `results/openrouter_luna/`): **38/38**, no extras, no wrong answer on the
blank question; 6–30 s per page. Every text page is 100 %:

| Page | 01 | 02 | 03 | 04 | 05 | 06 | 20 |
|---|---|---|---|---|---|---|---|
| Found | 4/4 | 5/5 | 6/6 | 6/6 | 5/5 | 7/7 | 5/5 (blank left null) |

Scorer fix: an option answered as "<label> (code N)", the way the shared prompt lists options, now counts as that
label. This also moves Gemma 4 26B (OpenRouter) from 31 to 32.

## Other models via OpenRouter (Oct 27)

`pipelines/openrouter_gemma.py` sends the original page as a base64 data URL with the direct prompt (`run`,
`run_moondream`, `run_mistral`, `run_luna`; answers capped at 1,000 tokens, 16,000 for Luna's reasoning). The free
`google/gemma-4-26b-a4b-it:free` tier was rate-limited upstream (HTTP 429) for minutes at a time, so the paid model
was used. Runs from Oct 27 onwards also save each raw reply.

| Page | Gemma 4 26B-A4B | Mistral Small 2603 | Moondream 3.1 | Gemma 3 4B |
|---|---|---|---|---|
| 01 | 4/4 | 0/4 | 1/4 | 0/4 |
| 02 | 5/5 | 2/5 | 2/5 | 0/5 |
| 03 | 4/6 | 0/6 | 2/6 | 0/6 |
| 04 | 2/6 | 1/6 | 0/6 | 0/6 |
| 05 | 5/5 | 1/5 | 0/5 | 1/5 |
| 06 | 7/7 | 1/7 | 0/7 | 0/7 |
| 20 | 5/5 | 4/5 | 2/5 | 2/5 |
| **Found** | **32/38** | 9/38 | 7/38 | 3/38 |
| Extras | 12 | 9 | 15 | 36 |

- **Gemma 4 26B** saw almost every circle. Three of its misses are small numbers and words on page 04 that it read
  wrong ("25,000" for 325,000, "$10 billion" for $19 billion, "inhaler" for inhale); seven of its 12 extras are
  uncircled words on page 03.
- **Mistral Small** listed headings, titles and dates ("DOT/P-10", "How the Pros Tamper with Jury Pools"), not the
  circled words. Page 06 hung with no answer cap until `max_tokens` was added; pages 06 and 20 were re-run.
- **Moondream 3.1** answered "NONE / NOTHING / ZERO / NIL" on page 03 and nearby headings on page 06.
- **Gemma 3 4B** listed each page's topic words ("Air", "Quality", "denitrification"), like a summary.

## Gemma 4 E2B, local (Oct 27)

`mlx-community/gemma-4-e2b-it-6bit` (bf16 10.2 GB and 8-bit 5.6 GB run out of GPU memory), thinking on,
`pipelines/gemma.py`: `run` (image + direct prompt) and `run_ocr` (the page's OCR text added to the prompt as
evidence for spelling; the model still decides what is circled). Page 06 of the image-only run ran out of GPU
memory and was re-run alone (`results/gemma_p6/`).

| Page | Image only | Image + OCR |
|---|---|---|
| 01 | 3/4: smoking, unobtrusive, Germantown | 3/4: smoking, unobtrusive, 92, + "no-smoking", "By-products" |
| 02 | 4/5 | 1/5 |
| 03 | 1/6 | **5/6**: incl. 32,000 and Rosenblatt, which most models miss |
| 04 | 1/6 | 1/6 |
| 05 | 1/5 ("toxic" for toxic waste) | 1/5 |
| 06 | 4/7 ("Martboro" for Marlboro) | 2/7 |
| 20 | 2/5 | 3/5 |
| **Found** | **16/38**, 3 extras | **16/38**, 5 extras |

It rarely reports anything that is not circled; its weakness is skipping circles. The OCR text fixes spelling and
helps on page 03 but makes it report fewer circles on pages 02 and 06. The two runs find different circles: their
union would reach about 21 of the 33 text-page circles (counted from saved predictions, not run as a pipeline).

## OCRia-1 via OpenDocRouter (Oct 27)

LlamaIndex's 4B document parser (built on Qwen3.5-4B), called through OpenDocRouter (`llamaindex/ocria-1`); the
weights are not public. It takes **no prompt**: each model runs a fixed transcription recipe, and the only switches
are the model and `layout`. Code: `experiments/opendocrouter/parse.py` (all pages), `score.py` (grading),
`simple_call.py` (one call with the official SDK). Cost about $0.004–0.007 per page, 3–7 s.

How circles show up in its Markdown:

- **Form options (page 20):** it writes `(circled)` after the chosen option, e.g. `- YES (circled)`, on all 5 marked
  answers, and nothing on the blank question. On the unmarked page the same options come out as empty `[ ]`
  checkboxes. 5/5, no extras.
- **Text pages:** no "circled" note. Circled words get formatting instead: underline `<u>`, highlight `<mark>`, or
  strikethrough `~~`. Its own prompt (technical report, appendix F) defines these as underline, highlighter and
  strikethrough, and has no tag for a circle.

| Counted as circled | Layout off | Layout on |
|---|---|---|
| `(circled)` only, as documented | **5/38**, 0 extras | 5/38, 0 extras |
| + `<mark>` + `~~` | 12/38, 2 extras | 7/38, 0 extras |
| + `<u>` as well | 27/38, 39 extras | 28/38, 42 extras |

Of the 61 formatted spans on the text pages (layout off), 22 are circled words, 4 are circles read too wide or
misread ("Framingham, Mass", "78%" for 76%), 17 are printed underlines and headings, 6 are words touched by the
top or bottom edge of a neighbouring red circle ("two weeks" above the "Circulation" circle), and 12 have no visible
cause. The format chosen for the same circle changes between runs (page 04: highlight with layout off, underline
with layout on). Circles on header lines ("1901", "D. M. Teng", "MARCH 11, 1996") get no formatting at all.
Conclusion: on forms its `(circled)` note is reliable; on free text a circle is indistinguishable from a printed
underline without another signal such as red-ink detection.

## Failure analysis: not seeing the circle vs. misreading it (text pages, 33 circles)

`tools/failure_analysis.py` splits each run's text-page results. **Misread** = something close to the circled text
was reported (the circle was seen, the text read wrong or cut short). **Missed** = nothing close. Extras are placed
on the clean page with OCR: next to a red circle (within about two lines), elsewhere on the page, or not printed on
the page at all.

| Run | Found | Misread | Missed | Extras: next to a circle | elsewhere | not on page |
|---|---|---|---|---|---|---|
| GPT-6 Luna | 33 | 0 | 0 | 0 | 0 | 0 |
| Gemma 4 26B-A4B | 27 | 3 | 3 | 2 | 5 | 2 |
| Qwen3-VL-2B, P6 tiles | 26 | 4 | 3 | 7 | 8 | 6 |
| Qwen3.5-4B, thinking on | 18 | 3 | 12 | 1 | 0 | 0 |
| Qwen3.5-4B, thinking off | 14 | 3 | 16 | 4 | 2 | 0 |
| Gemma 4 E2B, image only | 14 | 2 | 17 | 0 | 0 | 0 |
| Gemma 4 E2B, image + OCR | 13 | 1 | 19 | 1 | 2 | 0 |
| Qwen3-VL-2B, whole page | 12 | 2 | 19 | 24 | 38 | 1 |
| Florence-2, P7 | 15 | 2 | 16 | 0 | 0 | 2 |
| Mistral Small | 5 | 0 | 28 | 0 | 7 | 1 |
| Moondream 3.1 | 5 | 2 | 26 | 11 | 1 | 0 |
| Gemma 3 4B | 1 | 2 | 30 | 7 | 21 | 5 |

What it shows:

1. **Weak models do not see the circles.** Mistral, Gemma 3 4B and Qwen3-VL on the whole page miss most circles
   and fill the list with headings, topic words or whole sentences printed elsewhere on the page.
2. **Strong models see them but misread small text.** Gemma 4 26B and the tiled Qwen find nearly every circle;
   most of their losses are digits and letters in small print ("25,000", "$10 billion", "inbale") or a phrase cut
   short ("THE CARDIOVASCULAR").
3. **Zooming trades misses for fragments.** Tiles take Qwen3-VL from 19 missed to 3, but add made-up fragments
   ("ablatt", "le.") where a tile cuts a word.
4. **Cautious models skip rather than invent.** Gemma 4 E2B and Qwen3.5 with thinking report almost nothing that
   is not circled; Qwen3.5 thinking loses whole pages when its reasoning runs past the token budget.
5. The hardest circles are the small numbers on page 04 ("325,000", "$19 billion", missed by every local model and
   by Gemma 4 26B) and "32,000" / "Rosenblatt" on page 03. GPT-6 Luna reads all of them.

## Caveats

- Small sample: 7 pages, 39 items; differences of a few points are noise.
- Thresholds of P1 and P2 were chosen on the synthetic practice set, never on test pages. Some shared OCR/mapper
  fixes (stacked digits, question matching, erase-and-re-read) came from looking at failures on the test pages.
- Colour runs of SmolVLM2 P6/P7 were skipped for time (each would take over 20 minutes).
- Reproduce: `.venv_vlm/bin/python -m formeval.run --pipeline pipelines/<file>.py[:run_smolvlm|:run_florence] --ink black`;
  P2 needs the SAM 3 environment described in `pipelines/p2_ocr_sam3.py`.
