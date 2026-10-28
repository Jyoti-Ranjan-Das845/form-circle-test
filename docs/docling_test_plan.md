# Docling test plan: does any Docling setting signal a hand-drawn circle?

Docling is free (MIT code) and runs locally. Input: a page image or PDF. No prompt in the standard and VLM
pipelines; the extraction pipeline takes a template (field names) instead.

## What Docling can label (checked in its source)

The layout models (Heron, Egret) detect exactly 17 region types:
`caption, footnote, formula, list_item, page_footer, page_header, picture, section_header, table, text, title,
document_index, code, checkbox_selected, checkbox_unselected, form, key_value_region`.

The document format has more labels (`handwritten_text`, `grading_scale`, `marker`, `field_*`), but the layout
models do not output them; they come from other inputs (e.g. HTML forms) or a VLM.

`marker` = the symbol that introduces a list item or form field (a bullet, "1.", "a)"). It is not a pen mark.

## Signals we look for on each circled item

1. The circle's area gets its own region labelled `checkbox_selected`, `picture`, `form` or `key_value_region`.
2. A picture description or classification mentions a circle or mark.
3. The extraction pipeline returns the circled word when asked for "circled words".
4. The circled text is still read correctly (useful for a later pipeline even without a signal).

## Settings to test (one model loaded at a time; pages 04 and 20 first, all 7 if anything shows a signal)

| # | Pipeline | Setting | Why |
|---|---|---|---|
| D1 | Standard (layout + OCR) | defaults: Heron layout, automatic OCR | baseline: which labels appear around circles |
| D2 | Standard | full-page OCR mode | OCR everything, not only regions without embedded text |
| D3 | Standard | layout model Egret-large instead of Heron | bigger layout model, same 17 labels: may see `checkbox_selected` on circled options |
| D4 | Standard | OCR engine `ocrmac` (Apple Vision) vs `rapidocr` | text quality only; labels unchanged |
| D5 | Standard + enrichment | picture classification + picture description (small VLM describes each picture region) | if a circle is cut out as a `picture`, the description may mention it |
| D6 | VLM pipeline | `granite_docling` (258M), page to DocTags | one model reads the whole page; DocTags can express checkboxes |
| D7 | VLM pipeline | `smoldocling` (256M) | older sibling of D6 |
| D8 | Extraction pipeline | NuExtract-2B with template `{"circled_words": ["string"]}` | the only Docling mode driven by what you ask for |

Skipped: the `deepseek_ocr` VLM preset (3B, about 6.7 GB, does not fit next to anything else in 8 GB).

## Results (Oct 26)

Only the three settings that could plausibly signal a mark were run:

| Test | Setting | Result |
|---|---|---|
| 1 | Layout model (Heron default, Egret-large), page 20 | **No `checkbox_selected`** on any circled option; circled options come out as plain `text`. Heron drew a `picture` region over 2 of the 5 circles (Q1 YES, the "3"), Egret over 1. |
| 2 | GraniteDocling VLM pipeline, page 20 | **0 checkbox tags**; output degenerated into repeating "Whe" 300+ times. ~10 min including first download. |
| 3 | Extraction pipeline, NuExtract-2B, template `{"words_circled_in_red": ["string"]}` | **1 of 33** circles on the 6 text pages (only "THE CARDIOVASCULAR HAZARDS" on page 04). Pages 01, 02, 03, 05 returned an empty list (checked: the model's own answer); pages 04 and 06 returned whole sentences. Page 20 did not finish in 30 min on 8 GB (memory swapping). 2–7 min per page. |

Conclusion: no Docling setting reliably signals a hand-drawn circle; the layout model's occasional `picture`
region on a circle is the only hint.

## What the report shows per setting

For each of the 38 circles: the label(s) on that spot, whether the text was read correctly, and any description or
extracted value, plus seconds per page.
