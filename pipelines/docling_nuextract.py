"""Docling extraction pipeline (NuExtract-2B): the page image + a template naming what to extract.

Text pages: template {"words_circled_in_red": ["string"]}.
Form pages: one field per question, its options as the allowed values (NuExtract enum syntax).
Run from the Docling environment:
    .venv_docling/bin/python -m formeval.run --pipeline pipelines/docling_nuextract.py --ignore-context
"""
import json
import re

_extractor = None


def _get():
    global _extractor
    if _extractor is None:
        from docling.datamodel.base_models import InputFormat
        from docling.document_extractor import DocumentExtractor
        _extractor = DocumentExtractor(allowed_formats=[InputFormat.IMAGE])
    return _extractor


def _key(q):
    slug = re.sub(r"[^a-z0-9]+", "_", q["text"].lower()).strip("_")[:40]
    return f"{q['id']}__{slug}"


def _data(result):
    page = result.pages[0]
    data = getattr(page, "extracted_data", None)
    if data is None:
        raw = getattr(page, "raw_text", "") or ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}
    return data if isinstance(data, dict) else {}


def run(task):
    if task["kind"] == "text":
        data = _data(_get().extract(source=task["image_path"], template={"words_circled_in_red": ["string"]}))
        words = data.get("words_circled_in_red") or []
        words = words if isinstance(words, list) else [words]
        return {"marked": [{"text": str(w), "context": ""} for w in words if str(w).strip()]}

    questions = task["schema"]["questions"]
    template = {_key(q): [o["label"] for o in q.get("options", [])] or "string" for q in questions}
    data = _data(_get().extract(source=task["image_path"], template=template))
    answers = {}
    for q in questions:
        a = data.get(_key(q))
        answers[q["id"]] = (str(a) if a not in (None, "", []) and not isinstance(a, list) else
                            ([str(x) for x in a] if isinstance(a, list) and a else None))
    return {"answers": answers}
