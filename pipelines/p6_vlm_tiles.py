"""P6  VLM only, tiled: the page is cut into overlapping tiles and the VLM reads each tile itself. No OCR.

Functions: run (Qwen3-VL-2B), run_smolvlm (SmolVLM2-2.2B).
"""
from PIL import Image

from formeval.normalize import norm
from pipelines.common import vlm

TEXT_PROMPT = (
    "This is part of a scanned document page. A person may have circled some printed text by hand with a pen. "
    'Return a JSON list: [{"text": "<printed text inside a circle>", "context": "<the full printed line it is on>"}]. '
    "Return [] if nothing in this image is circled. Output only the JSON."
)
OPTIONS_PROMPT = (
    "This is part of a scanned questionnaire page. A person has circled their choices by hand with a pen. "
    "For the questions below that are visible in this image, give the option(s) that are circled. "
    'Return JSON: {"<question id>": "<option label>"}; use a list for multi-select; leave out questions '
    "you cannot see or that have nothing circled. Output only the JSON.\n\nQuestions:\n"
)


def _tile_images(path):
    img = Image.open(path).convert("RGB")
    for box in vlm.tiles(img.width, img.height):
        tile = img.crop(box)
        yield tile.resize((tile.width * 2, tile.height * 2))


def _run(task):
    path = task["image_path"]
    if task["kind"] == "text":
        marked, seen = [], set()
        for tile in _tile_images(path):
            items = vlm.parse_json(vlm.ask(tile, TEXT_PROMPT, max_tokens=250)) or []
            for it in items if isinstance(items, list) else []:
                if isinstance(it, dict) and isinstance(it.get("text"), str) and it["text"].strip():
                    key = (norm(it["text"]), norm(it.get("context") or ""))
                    if key not in seen:
                        seen.add(key)
                        marked.append({"text": it["text"], "context": str(it.get("context") or "")})
        return {"marked": marked}

    prompt = OPTIONS_PROMPT + vlm.schema_text(task["schema"])
    votes = {}
    for tile in _tile_images(path):
        data = vlm.parse_json(vlm.ask(tile, prompt, max_tokens=300)) or {}
        for qid, a in (data.items() if isinstance(data, dict) else []):
            if a not in (None, "", []):
                votes.setdefault(qid, []).append(a)
    answers = {}
    for q in task["schema"]["questions"]:
        got = votes.get(q["id"], [])
        if q["select"] == "many":
            answers[q["id"]] = sorted({str(x) for a in got for x in (a if isinstance(a, list) else [a])})
        else:
            flat = [str(a[0]) if isinstance(a, list) and a else str(a) for a in got]
            answers[q["id"]] = max(set(flat), key=flat.count) if flat else None
    return {"answers": answers}


def run(task):
    vlm.use("qwen")
    return _run(task)


def run_smolvlm(task):
    vlm.use("smolvlm")
    return _run(task)
