"""Local small vision models on MLX, shared by the VLM pipelines.

Pick the model with use(...) before the first call:
    qwen      Qwen3-VL-2B-Instruct (bf16, original precision)   free prompts + grounding boxes
    smolvlm   SmolVLM2-2.2B-Instruct          free prompts, faster family
    florence  Florence-2-large-ft (bf16, original precision)  fixed task tokens only (<OCR>, <MORE_DETAILED_CAPTION>, ...)
"""
import json
import re
import tempfile
from pathlib import Path

MODELS = {
    "qwen": "mlx-community/Qwen3-VL-2B-Instruct-bf16",
    "smolvlm": "mlx-community/SmolVLM2-2.2B-Instruct-mlx",
    "florence": "mlx-community/Florence-2-large-ft-bf16",
    "gemma": "mlx-community/gemma-4-e2b-it-6bit",   # bf16 (10.2 GB) and 8-bit (5.6 GB) exceed the GPU memory limit on 8 GB
    "qwen35": "mlx-community/Qwen3.5-4B-6bit",      # bf16 (9.1 GB) and 8-bit (5.1 GB) exceed the GPU memory limit on 8 GB
    "qwen35_think": "mlx-community/Qwen3.5-4B-6bit",  # same weights, reasoning mode on
}
THINKING = {"gemma", "qwen35_think"}  # models run with their reasoning mode on
NO_THINKING = {"qwen35"}  # thinks by default; switched off for direct (Instruct-style) answers
_name = "qwen"
_loaded = None
last_full = ""  # the last reply including any reasoning block, for inspection


def use(name):
    global _name, _loaded
    if name != _name:
        same_weights = _name in MODELS and MODELS[_name] == MODELS[name]
        _name, _loaded = name, (_loaded if same_weights else None)


def current():
    return _name


def _model():
    global _loaded
    if _loaded is None:
        from mlx_vlm import load
        _loaded = load(MODELS[_name])
    return _loaded


def _as_path(image):
    if isinstance(image, (str, Path)):
        return str(image)
    tmp = Path(tempfile.mkdtemp()) / "img.png"
    image.save(tmp)
    return str(tmp)


def ask(image, prompt, max_tokens=300):
    """image: a path or a PIL image. For florence, `prompt` is a task token such as "<OCR>"."""
    from mlx_vlm import generate
    from mlx_vlm.prompt_utils import apply_chat_template

    model, processor = _model()
    if _name == "florence":
        chat = prompt
    elif _name in THINKING:
        chat = apply_chat_template(processor, model.config, prompt, num_images=1, enable_thinking=True)
    elif _name in NO_THINKING:
        chat = apply_chat_template(processor, model.config, prompt, num_images=1, enable_thinking=False)
    else:
        chat = apply_chat_template(processor, model.config, prompt, num_images=1)
    res = generate(model, processor, chat, image=[_as_path(image)], max_tokens=max_tokens, temperature=0.0,
                   verbose=False)
    global last_full
    text = last_full = res.text if hasattr(res, "text") else str(res)
    if _name == "gemma":  # keep only the final answer after the reasoning block
        text = re.split(r"<channel\|>", text)[-1].replace("<turn|>", "").strip()
    elif _name in THINKING:  # no </think> means the reasoning ran out of tokens: there is no answer
        text = text.split("</think>", 1)[1].strip() if "</think>" in text else ""
    return text


def florence_boxes(text, width, height):
    """Florence-2 answers boxes as <loc_x1><loc_y1><loc_x2><loc_y2> on a 0-999 grid; return pixel boxes."""
    vals = [int(v) for v in re.findall(r"<loc_(\d+)>", text)]
    return [[round(vals[i] / 999 * width), round(vals[i + 1] / 999 * height),
             round(vals[i + 2] / 999 * width), round(vals[i + 3] / 999 * height)] for i in range(0, len(vals) - 3, 4)]


def parse_json(text):
    """First JSON object or list in the text, or None."""
    text = re.sub(r"```(?:json)?", "", text)
    for opener, closer in (("[", "]"), ("{", "}")):
        start = text.find(opener)
        while start >= 0:
            depth = 0
            for i, ch in enumerate(text[start:], start):
                depth += ch == opener
                depth -= ch == closer
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
            start = text.find(opener, start + 1)
    return None


def tiles(width, height, cols=2, rows=3, overlap=0.12):
    """Overlapping tile boxes covering the page."""
    tw, th = width / cols, height / rows
    ox, oy = tw * overlap, th * overlap
    out = []
    for r in range(rows):
        for c in range(cols):
            out.append([int(max(0, c * tw - ox)), int(max(0, r * th - oy)),
                        int(min(width, (c + 1) * tw + ox)), int(min(height, (r + 1) * th + oy))])
    return out


def schema_text(schema):
    lines = []
    for q in schema["questions"]:
        opts = " | ".join(o["label"] + (f" (code {o['code']})" if o.get("code") else "") for o in q.get("options", []))
        lines.append(f'- "{q["id"]}" ({q["select"]}): {q["text"]}  options: {opts or "(free text)"}')
    return "\n".join(lines)
