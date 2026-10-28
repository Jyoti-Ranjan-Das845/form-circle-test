"""Whole page -> Qwen3-VL-2B (4-bit, local MLX). One call per page, prompt = the task's own instruction.

Run in the MLX environment:
    .venv_vlm/bin/python -m formeval.run --pipeline pipelines/qwen3vl_2b.py
"""
import json
import re

MODEL = "mlx-community/Qwen3-VL-2B-Instruct-4bit"
_loaded = None


def _model():
    global _loaded
    if _loaded is None:
        from mlx_vlm import load
        model, processor = load(MODEL)
        _loaded = (model, processor)
    return _loaded


def _schema_text(schema):
    lines = []
    for q in schema["questions"]:
        opts = " | ".join(o["label"] for o in q.get("options", [])) or "(free text)"
        lines.append(f'- id "{q["id"]}" ({q["select"]}): {q["text"]}  options: {opts}')
    return "\n".join(lines)


def _json_obj(text):
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        depth += ch == "{"
        depth -= ch == "}"
        if depth == 0:
            try:
                return json.loads(text[start:i + 1])
            except json.JSONDecodeError:
                return None
    return None


def run(task):
    from mlx_vlm import generate
    from mlx_vlm.prompt_utils import apply_chat_template

    model, processor = _model()
    prompt = task["instruction"]
    if task["kind"] == "options":
        prompt += "\n\nQuestions:\n" + _schema_text(task["schema"])
    chat = apply_chat_template(processor, model.config, prompt, num_images=1)
    res = generate(model, processor, chat, image=[task["image_path"]],
                   max_tokens=400 if task["kind"] == "text" else 600, temperature=0.0, verbose=False)
    data = _json_obj(res.text if hasattr(res, "text") else str(res)) or {}

    if task["kind"] == "text":
        marked = []
        for m in data.get("marked", []) if isinstance(data.get("marked"), list) else []:
            if isinstance(m, dict) and isinstance(m.get("text"), str):
                marked.append({"text": m["text"], "context": str(m.get("context") or "")})
            elif isinstance(m, str):
                marked.append({"text": m, "context": ""})
        return {"marked": marked}

    raw = data.get("answers", data) if isinstance(data, dict) else {}
    answers = {}
    for q in task["schema"]["questions"]:
        a = raw.get(q["id"]) if isinstance(raw, dict) else None
        if isinstance(a, list):
            a = [str(x) for x in a]
        elif a is not None:
            a = str(a)
        answers[q["id"]] = a
    return {"answers": answers}
