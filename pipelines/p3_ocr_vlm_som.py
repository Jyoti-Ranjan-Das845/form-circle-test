"""P3  OCR + VLM with Set-of-Mark prompting.

OCR -> a number tag drawn at the start of every printed line -> the VLM names which tagged lines contain
hand-circled text and what that text is -> snapped to the OCR words of that line -> mapper.
Functions: run (Qwen3-VL-2B), run_smolvlm (SmolVLM2-2.2B).
"""
from PIL import Image, ImageDraw, ImageFont

from formeval.normalize import norm
from pipelines.common import mapper, ocr, vlm

SCALE = 1.5
PROMPT = (
    "This is a scanned document page. Every printed line has a small number tag like [12] at its left. "
    "A person has circled some printed text by hand with a pen. Return a JSON list with one entry per circle: "
    '[{"line": <tag number>, "text": "<the printed text inside the circle>"}]. '
    "Return [] if nothing is circled. Output only the JSON."
)


def _tagged(path, page):
    img = Image.open(path).convert("RGB")
    img = img.resize((int(img.width * SCALE), int(img.height * SCALE)))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=12)
    for i, line in enumerate(page["lines"]):
        x1, y1 = line["box"][0] * SCALE, line["box"][1] * SCALE
        tag = f"[{i}]"
        tw = d.textlength(tag, font=font)
        x = max(0, x1 - tw - 3)
        d.rectangle([x, y1, x + tw + 2, y1 + 13], fill=(255, 255, 230))
        d.text((x + 1, y1), tag, fill=(0, 90, 0), font=font)
    return img


def snap(page, line_idx, text):
    """OCR words whose text appears in the VLM's answer, on the tagged line or a neighbour (tags on dense
    pages are easy to misread by one or two); the line with the most matched characters wins."""
    want = norm(text)
    best = []
    for li in sorted(range(line_idx - 2, line_idx + 3), key=lambda k: abs(k - line_idx)):
        ids = [i for i, w in enumerate(page["words"]) if w["line"] == li and norm(w["text"]) and norm(w["text"]) in want]
        if sum(len(page["words"][i]["text"]) for i in ids) > sum(len(page["words"][i]["text"]) for i in best):
            best = ids
    return best


def _run(task):
    page = ocr.read(task["image_path"])
    items = vlm.parse_json(vlm.ask(_tagged(task["image_path"], page), PROMPT, max_tokens=300)) or []
    groups = []
    for it in items if isinstance(items, list) else []:
        if isinstance(it, dict) and str(it.get("line", "")).strip().lstrip("[").rstrip("]").isdigit():
            li = int(str(it["line"]).strip("[] "))
            if 0 <= li < len(page["lines"]):
                ids = snap(page, li, str(it.get("text", "")))
                if ids:
                    groups.append(ids)
    return mapper.answer(task, page, groups)


def run(task):
    vlm.use("qwen")
    return _run(task)


def run_smolvlm(task):
    vlm.use("smolvlm")
    return _run(task)
