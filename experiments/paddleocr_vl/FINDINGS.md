# PaddleOCR-VL-1.6 probe: page 04 (two-column journal page, 6 red circles)

Run with `probe.py 04` on an M2 / 8 GB Mac (MLX-VLM backend): both runs together took about 3.5 minutes.
Outputs are in `out/04/` (`overlay.png`: red = real circles, blue = layout regions, green = spotting lines).

## Run 1: full pipeline (layout detection on)

- **No circle became its own region.** 18 regions, all ordinary labels
  (`doc_title`, `text`, `paragraph_title`, `abstract`, `header`, `footer`, `footnote`, `number`).
  The only circle with a matching region is "THE CARDIOVASCULAR HAZARDS", which is a heading region anyway.
- **All 6 circled items were read** inside their paragraphs: Framingham, THE CARDIOVASCULAR HAZARDS, inhale,
  325,000, $19 billion, Boston.
- **Nothing says "circled"** anywhere in the JSON or Markdown, and the red ink is not mentioned.
- **The circles leave small traces in the text:** "325,000" became "**$**325,000" (the left arc read as a $),
  "inhale." became "inhale. **i.**", and the comma after the circled "Framingham" was lost.

## Run 2: layout off, `prompt_label="spotting"`

- **Positions are per line, not per word** (88 lines). The circled word is always inside a full line,
  e.g. `'to 325,000 premature deaths each year. The'`.
- **No circle became its own piece.** "inhale." has its own entry only because it is alone on its line.
- One circle damaged the reading: "Boston" was read as "**Luston**" in this run (run 1 read it correctly).

## Takeaway

PaddleOCR-VL reads the page well but ignores the marks: the circle is neither a region, a piece, nor a flag.
To get "what is circled" we need a separate step that sees the marks, then matches them to the text.
Spotting gives only line positions, so finding the exact circled word inside a line needs word-level
positions (or a crop of the circled area).
