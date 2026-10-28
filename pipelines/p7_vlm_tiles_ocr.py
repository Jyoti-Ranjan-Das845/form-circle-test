"""P7  VLM locates (tiled) + OCR reads: the VLM returns boxes of hand-drawn circles per tile, OCR words
inside each box are the answer.

Functions: run (Qwen3-VL-2B), run_smolvlm (SmolVLM2-2.2B), run_florence (Florence-2 open-vocabulary
detection of "hand-drawn circle").
"""
from PIL import Image

from pipelines.common import mapper, ocr, vlm

PROMPT = ("This is part of a scanned document page. Locate every hand-drawn pen circle drawn around printed text. "
          'Output a JSON list: [{"bbox_2d": [x1, y1, x2, y2]}]. Output [] if there is none. Output only the JSON.')


def _boxes_in_tile(tile):
    """Boxes in tile pixel coordinates."""
    w, h = tile.size
    if vlm.current() == "florence":
        return vlm.florence_boxes(vlm.ask(tile, "<OPEN_VOCABULARY_DETECTION>hand-drawn circle", max_tokens=120), w, h)
    items = vlm.parse_json(vlm.ask(tile, PROMPT, max_tokens=250)) or []
    out = []
    for it in items if isinstance(items, list) else []:
        b = it.get("bbox_2d") if isinstance(it, dict) else it
        if isinstance(b, list) and len(b) == 4 and all(isinstance(v, (int, float)) for v in b):
            scale = (w, h) if max(b) <= 1.0 else (w / 1000, h / 1000)   # 0-1 floats or Qwen's 0-1000 grid
            out.append([b[0] * scale[0], b[1] * scale[1], b[2] * scale[0], b[3] * scale[1]])
    return out


def _run(task):
    path = task["image_path"]
    page = ocr.read(path)
    img = Image.open(path).convert("RGB")
    groups = []
    for tx1, ty1, tx2, ty2 in vlm.tiles(img.width, img.height):
        tile = img.crop((tx1, ty1, tx2, ty2))
        f = 2
        for b in _boxes_in_tile(tile.resize((tile.width * f, tile.height * f))):
            box = [tx1 + b[0] / f, ty1 + b[1] / f, tx1 + b[2] / f, ty1 + b[3] / f]
            ids = mapper.words_in_box(page, box, min_inside=0.6)
            if ids and len(ids) <= 15 and ids not in groups:
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
