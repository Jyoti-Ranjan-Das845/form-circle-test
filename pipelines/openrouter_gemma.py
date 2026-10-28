"""Vision models through OpenRouter: the original page image embedded in the request + a short prompt.

Functions: run (google/gemma-4-26b-a4b-it), run_moondream (moondream/moondream3.1-9b-a2b),
run_mistral (mistralai/mistral-small-2603), run_luna (openai/gpt-6-luna, medium reasoning effort).

Needs OPENROUTER_API_KEY in .env (project root). Run:
    .venv_vlm/bin/python -m formeval.run --pipeline pipelines/openrouter_gemma.py --ignore-context
"""
import base64
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from pipelines.common.vlm import parse_json, schema_text

MODEL = "google/gemma-4-26b-a4b-it"
URL = "https://openrouter.ai/api/v1/chat/completions"
TEXT_PROMPT = "Can you identify which words are circled in red in the image? Reply with a JSON list of the words."
OPTIONS_PROMPT = ("The right answer to each question is marked with a red circle. If nothing is circled for a question, "
                  "the answer is null. Reply with all the answers you can see in the image, as JSON "
                  '{"<question id>": "<answer>"}.\n\nQuestions:\n')
ROOT = Path(__file__).resolve().parent.parent


def _key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.strip().startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY is empty in .env")


def ask(image_path, prompt, retries=15, model=None, extra=None):
    data_url = "data:image/png;base64," + base64.b64encode(Path(image_path).read_bytes()).decode()
    body = {"model": model or MODEL, "max_tokens": 1000, "messages": [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": data_url}}]}], **(extra or {})}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"] or ""
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503) and attempt < retries - 1:   # free tier rate limits / busy provider
                time.sleep(60)  # the free model is often rate-limited upstream for minutes at a time
                continue
            raise RuntimeError(f"OpenRouter HTTP {e.code}: {e.read()[:300]!r}") from e


def run(task, model=None, extra=None):
    time.sleep(2)  # small gap between requests
    if task["kind"] == "text":
        raw = ask(task["image_path"], TEXT_PROMPT, model=model, extra=extra)
        data = parse_json(raw)
        if isinstance(data, list):
            items = [str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in data]
        else:
            items = re.findall(r'"([^"\n]+)"', raw) or [l.strip(" -*•\"',[]\t") for l in raw.splitlines()]
        if len(items) == 1 and ", " in items[0]:
            items = items[0].split(", ")
        seen, marked = set(), []
        for t in (x.strip() for x in items):
            if t and t.lower() not in seen:
                seen.add(t.lower())
                marked.append({"text": t, "context": ""})
        return {"marked": marked, "raw": raw}

    raw = ask(task["image_path"], OPTIONS_PROMPT + schema_text(task["schema"]), model=model, extra=extra)
    data = parse_json(raw)
    data = data if isinstance(data, dict) else {}
    answers = {}
    for q in task["schema"]["questions"]:
        a = data.get(q["id"])
        if isinstance(a, list):
            a = [str(x) for x in a]
        elif a is None or str(a).lower() in ("null", "none", ""):
            a = None
        else:
            a = str(a)
        answers[q["id"]] = a
    return {"answers": answers, "raw": raw}


def run_moondream(task):
    return run(task, model="moondream/moondream3.1-9b-a2b")


def run_mistral(task):
    return run(task, model="mistralai/mistral-small-2603")


def run_luna(task):
    # reasoning tokens count against max_tokens, so give room for them
    return run(task, model="openai/gpt-6-luna", extra={"reasoning": {"effort": "medium"}, "max_tokens": 16000})
