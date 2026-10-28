"""Gemma 4 E2B (6-bit, thinking on), original colour page.

run      Gemma only: the image + a short prompt.
run_ocr  OCR + Gemma: the image + the page's OCR text as evidence for spelling; Gemma decides what is circled.
"""
import re

from pipelines.common import ocr, vlm

TEXT_PROMPT = "Can you identify which words are circled in red in the image? Reply with a JSON list of the words."
OPTIONS_PROMPT = ("The right answer to each question is marked with a red circle. If nothing is circled for a question, "
                  "the answer is null. Reply with all the answers you can see in the image, as JSON "
                  '{"<question id>": "<answer>"}.\n\nQuestions:\n')
OCR_NOTE = ("\n\nOCR text of this page (extracted evidence; it may contain reading errors and does not show the "
            "circles; use it only to spell the words correctly):\n")
MAX_TOKENS = 1500  # room for the reasoning block plus the answer


def _words(raw):
    data = vlm.parse_json(raw)
    if isinstance(data, list):
        items = [str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in data]
    else:
        items = re.findall(r'"([^"\n]+)"', raw) or [l.strip(" -*•\"',[]\t") for l in raw.splitlines()]
    if len(items) == 1 and ", " in items[0]:
        items = items[0].split(", ")
    seen, out = set(), []
    for t in (x.strip() for x in items):
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append({"text": t, "context": ""})
    return out


def _answers(raw, schema):
    data = vlm.parse_json(raw)
    data = data if isinstance(data, dict) else {}
    answers = {}
    for q in schema["questions"]:
        a = data.get(q["id"])
        if isinstance(a, list):
            a = [str(x) for x in a]
        elif a is None or str(a).lower() in ("null", "none", ""):
            a = None
        else:
            a = str(a)
        answers[q["id"]] = a
    return answers


def _run(task, with_ocr):
    vlm.use("gemma")
    note = ""
    if with_ocr:
        note = OCR_NOTE + "\n".join(l["text"] for l in ocr.read(task["image_path"])["lines"])
    if task["kind"] == "text":
        return {"marked": _words(vlm.ask(task["image_path"], TEXT_PROMPT + note, max_tokens=MAX_TOKENS))}
    raw = vlm.ask(task["image_path"], OPTIONS_PROMPT + vlm.schema_text(task["schema"]) + note, max_tokens=MAX_TOKENS)
    return {"answers": _answers(raw, task["schema"])}


def run(task):
    return _run(task, with_ocr=False)


def run_ocr(task):
    return _run(task, with_ocr=True)
