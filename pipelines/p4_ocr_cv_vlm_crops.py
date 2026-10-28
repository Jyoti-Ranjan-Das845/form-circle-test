"""P4  OCR + classical CV + VLM: the mark finder proposes spots (loose setting), a VLM judges each
enlarged crop, OCR supplies the exact words.

Functions: run (Qwen3-VL-2B), run_smolvlm (SmolVLM2-2.2B), run_florence (Florence-2 <DETAILED_CAPTION>, the caption mode that works in the MLX build:
a spot counts when the caption mentions a circle).
"""
import re

import cv2
from PIL import Image

from formeval.normalize import norm
from pipelines.common import mapper, marks_cv, ocr, vlm

MAX_SPOTS = 12
PROMPT = ("Is there a hand-drawn pen circle drawn around some printed text in this image? "
          "If yes, reply with exactly the printed text inside the circle. If no, reply NONE.")
CIRCLE_WORDS = re.compile(r"\b(circle[sd]?|circling|ring|loop|oval|encircl\w*)\b", re.I)


def _crop(path, box, th):
    img = Image.open(path).convert("RGB")
    m = int(0.6 * th)
    x1, y1, x2, y2 = box
    crop = img.crop((max(0, x1 - m), max(0, y1 - m), min(img.width, x2 + m), min(img.height, y2 + m)))
    s = 448 / max(crop.size)
    return crop.resize((max(1, int(crop.width * s)), max(1, int(crop.height * s))))


def _run(task):
    path = task["image_path"]
    first = ocr.read(path)
    cands = marks_cv.candidates(path, first, loose=True)[:MAX_SPOTS]
    shape = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE).shape
    page = ocr.best_reading(ocr.read_without(path, marks_cv.stroke_mask(shape, cands)), first) if cands else first
    th = marks_cv._text_height(page)
    groups = []
    for c in cands:
        inside = mapper.words_in_polygon(page, c["hull"], min_inside=0.5)
        if not inside:
            continue
        if vlm.current() == "florence":
            caption = vlm.ask(_crop(path, c["box"], th), "<DETAILED_CAPTION>", max_tokens=80)
            if CIRCLE_WORDS.search(caption):
                groups.append(inside)
            continue
        answer = vlm.ask(_crop(path, c["box"], th), PROMPT, max_tokens=40).strip()
        if not answer or norm(answer).startswith("none"):
            continue
        want = norm(answer)
        ids = [i for i in inside if norm(page["words"][i]["text"]) and norm(page["words"][i]["text"]) in want]
        if ids:
            groups.append(ids)
    return mapper.answer(task, page, groups)


def run(task):
    vlm.use("qwen")
    return _run(task)


def run_smolvlm(task):
    vlm.use("smolvlm")
    return _run(task)


def run_florence(task):
    vlm.use("florence")
    return _run(task)
