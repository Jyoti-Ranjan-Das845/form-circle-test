# Qwen3-VL-2B (4-bit, local MLX) probe: page 04 (two-column journal page, 6 red circles)

Setup: `uv venv .venv_vlm && uv pip install --python .venv_vlm/bin/python mlx-vlm Pillow numpy`,
model `mlx-community/Qwen3-VL-2B-Instruct-4bit` (1.7 GB). Run: `.venv_vlm/bin/python experiments/qwen3vl/probe.py 04`.
Machine: M2, 8 GB. Outputs in `out/04/` (`grounded_*.png`: red = real circles, green = model's boxes).

| Run | Time | Result |
|---|---|---|
| direct, colour | 4.7 s | 1 of 6 ("THE CARDIOVASCULAR HAZARDS") plus a whole paragraph that was not circled |
| direct, grey | 3.6 s | returned the byline line "William B. Kannel, M.D. Framingham, Mass." (contains 1 of 6) |
| grounded, colour | 4.0 s | 1 box, not on any circle; label just echoed the prompt template |
| grounded, grey | 4.1 s | 1 box, not on any circle |

Model load: 2.7 s. About 800 prompt tokens per call (the page is shrunk to fit), 15–90 output tokens.

## Takeaway

Latency and cost are fine (≈4 s per page, $0, runs on the laptop), but at this size the model cannot see
which text is circled on a dense page: it mostly guesses salient text (a heading, a paragraph) and its boxes
miss every circle. Colour did not help either. Next things to try: give it more pixels (upscale or crop),
the 8-bit or 4B variant, or let it judge small crops instead of the whole page.
