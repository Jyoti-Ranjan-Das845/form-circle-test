# Manual tests: Qwen3-VL-2B in Ollama (both Q4_K_M, 4-bit)

Prompt (text pages): "Can you identify which words are circled in red in the image?" + the marked page.
Prompt (page 20): "The right answer to each question is marked with a red circle. Which answers are circled?"
Raw Instruct answers: `experiments/ollama/qwen3-vl_2b-instruct/`.

| Page | Circled (expected) | `qwen3-vl:2b` (thinking, run by hand) | `qwen3-vl:2b-instruct` | Instruct: not circled but reported |
|---|---|---|---|---|
| 01 | Germantown · smoking · 92 · unobtrusive | Germantown (+ unobtrusive circle misread as "nonbreathing") → **1 / 4** | smoking · unobtrusive → **2 / 4** | 23 · 70 |
| 02 | D. M. Teng · 1901 · 50-liter · 20 hours · pH | 1901 · D. M. Teng · 50-liter → **3 / 5** | 50-liter · 20 hours · pH → **3 / 5** | 28-liter · Cellulase · 500-liter |
| 03 | Circulation · 32,000 · statistical bias · NADA · Rosenblatt · SMOKERS | NADA · SMOKERS → **2 / 6** | NADA (listed 6 times) → **1 / 6** | – |
| 04 | Framingham · THE CARDIOVASCULAR HAZARDS · inhale · 325,000 · $19 billion · Boston | Framingham · heading → **2 / 6** | heading · "inhal" → **2 / 6** | the |
| 05 | Kevin Sweeney · MARCH 11, 1996 · weak · toxic waste · Bacon | MARCH 11, 1996 · weak ("very weak") → **2 / 5** | weak · toxic waste → **2 / 5** | August 1 · S,H&B · conformance · a phrase |
| 06 | 24.4% · Marlboro · not · 4.6% · BIAD #93-13104 · 18.5% · 76% | not tested | 4.6% · 24.4% · 76% → **3 / 7** | 2.0% · 3.5% · 5.0% |
| 20 | Q1 YES · Feb–June NO · July YES · (Aug–Oct blank) · Nov–Jan NO · weekends 3 | not tested | July YES · weekends 3 → **2 / 5** | answered YES for every month, incl. the blank one |
| **Total** | 38 circles | **10 / 26** (pages 1–5) | **15 / 38** (pages 1–5: **10 / 26**) | |
