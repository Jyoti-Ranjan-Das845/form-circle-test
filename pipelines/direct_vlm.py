"""Direct: the original page image + one short prompt to a VLM. No OCR, no tiles, no extra steps.

Functions: run (Qwen3-VL-2B), run_smolvlm (SmolVLM2-2.2B), run_qwen35 / run_qwen35_think
(Qwen3.5-4B, 6-bit, thinking off / on).
"""
import re

from pipelines.common import vlm

TEXT_PROMPT = "Can you identify which words are circled in red in the image? Reply with a JSON list of the words."
OPTIONS_PROMPT = ("The right answer to each question is marked with a red circle. If nothing is circled for a question, "
                  "the answer is null. Reply with all the answers you can see in the image, as JSON "
                  '{"<question id>": "<answer>"}.\n\nQuestions:\n')


TEXT_KEYS = ("text", "text_content", "word", "label")  # Qwen models sometimes answer [{"bbox_2d": ..., "text_content": ...}]


def _item_text(x):
    if not isinstance(x, dict):
        return str(x)
    return str(next((x[k] for k in TEXT_KEYS if isinstance(x.get(k), str)),
                    next((v for v in x.values() if isinstance(v, str)), "")))


def words(raw):
    """The circled words from a text-page reply: a JSON list of strings or objects, or whatever can be salvaged."""
    data = vlm.parse_json(raw)
    fields = re.findall(rf'"(?:{"|".join(TEXT_KEYS)})"\s*:\s*"([^"\n]+)"', raw)
    if fields:  # objects with a text field; also works when the reply was cut off mid-list
        items = fields
    elif isinstance(data, list) and not all(isinstance(x, (int, float)) for x in data):  # skip a bare box [x1, y1, ...]
        items = [_item_text(x) for x in data]
    else:  # cut-off or not JSON: take the quoted strings, else the lines
        items = (re.findall(r'"([^"\n]+)"', raw)
                 or [l.strip(" -*•\"',[]\t") for l in re.sub(r"```\w*", "", raw).splitlines()])
    if len(items) == 1 and ", " in items[0]:  # everything in one comma-separated string
        items = items[0].split(", ")
    seen, marked = set(), []
    for t in (x.strip() for x in items):
        if t and t.lower() not in seen:  # the model sometimes repeats one answer until it runs out of tokens
            seen.add(t.lower())
            marked.append({"text": t, "context": ""})
    return marked


def _run(task, max_tokens=(200, 300)):
    if task["kind"] == "text":
        raw = vlm.ask(task["image_path"], TEXT_PROMPT, max_tokens=max_tokens[0])
        return {"marked": words(raw), "raw": vlm.last_full}  # raw: the model's full reply, kept for inspection

    raw = vlm.ask(task["image_path"], OPTIONS_PROMPT + vlm.schema_text(task["schema"]), max_tokens=max_tokens[1])
    data = vlm.parse_json(raw)
    data = data if isinstance(data, dict) else {}
    answers = {}
    for q in task["schema"]["questions"]:
        a = data.get(q["id"])
        if isinstance(a, list):
            a = [str(x) for x in a]
        elif a is not None and str(a).lower() not in ("null", "none", ""):
            a = str(a)
        else:
            a = None
        answers[q["id"]] = a
    return {"answers": answers, "raw": vlm.last_full}


def run(task):
    vlm.use("qwen")
    return _run(task)


def run_smolvlm(task):
    vlm.use("smolvlm")
    return _run(task)


def run_qwen35(task):
    vlm.use("qwen35")
    return _run(task)


def run_qwen35_think(task):
    vlm.use("qwen35_think")
    return _run(task, max_tokens=(8000, 8000))  # room for the reasoning block plus the answer (4,000 ran out on long pages)
