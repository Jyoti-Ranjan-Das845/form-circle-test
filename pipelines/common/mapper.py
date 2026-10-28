"""Turn "these words are circled" into the evaluator contract.

Every pipeline ends here, so the comparison is about how well each one finds the marks.
`groups` is a list of circled word groups; each group is a list of indices into ocr["words"]
(one group per circle).
"""
import re

import numpy as np

from formeval.normalize import norm

STOP = {"the", "a", "an", "of", "to", "in", "or", "and", "is", "are", "was", "do", "did", "you", "your", "for",
        "on", "at", "it", "any", "if", "that", "this", "with", "be", "have", "has", "following"}


def words_in_polygon(ocr, polygon, min_inside=0.75):
    """Indices of OCR words whose box lies mostly inside the polygon (list of (x, y))."""
    import cv2

    poly = np.array(polygon, dtype=np.float32).reshape(-1, 1, 2)
    hits = []
    for i, w in enumerate(ocr["words"]):
        x1, y1, x2, y2 = w["box"]
        pts = [(x1 + (x2 - x1) * fx, y1 + (y2 - y1) * fy) for fx in (0.2, 0.5, 0.8) for fy in (0.3, 0.7)]
        inside = sum(cv2.pointPolygonTest(poly, (float(px), float(py)), False) >= 0 for px, py in pts)
        if inside / len(pts) >= min_inside:
            hits.append(i)
    return hits


def words_in_box(ocr, box, min_inside=0.75):
    x1, y1, x2, y2 = box
    return words_in_polygon(ocr, [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], min_inside)


def _reading_order(ocr, idxs):
    return sorted(set(idxs), key=lambda i: (ocr["words"][i]["line"], ocr["words"][i]["box"][0]))


def text_answer(ocr, groups):
    marked, seen = [], set()
    for g in groups:
        idxs = [i for i in _reading_order(ocr, g) if i not in seen]
        if not idxs:
            continue
        seen.update(idxs)
        text = " ".join(ocr["words"][i]["text"] for i in idxs)
        context = ocr["lines"][ocr["words"][idxs[0]]["line"]]["text"]
        marked.append({"text": text, "context": context})
    return {"marked": marked}


def _tokens(s):
    return [t for t in re.findall(r"[a-z0-9][a-z0-9.\-%$/]*", norm(s)) if t not in STOP]


def _anchor_line(ocr, question, weights):
    """The OCR line that best matches the question text. Tokens shared by many questions count less;
    question numbering like "1.2.3" counts most."""
    q = {t.rstrip(".") for t in _tokens(question["text"])}
    best, best_score = None, 0.0
    for li, line in enumerate(ocr["lines"]):
        lt = {x.rstrip(".") for x in _tokens(line["text"])}
        score = sum(3.0 if re.match(r"^\d+(\.\d+)+$|^[a-z]?\d+[a-z]?$", t) else weights.get(t, 1.0) for t in q & lt)
        if score > best_score:
            best, best_score = li, score
    return best


def _option_hits(ocr, option, word_ids):
    """Word indices (within word_ids) that spell the option label, or its printed code."""
    label = _tokens(option["label"]) or [norm(option["label"])]
    words = [(i, norm(ocr["words"][i]["text"]).strip(".,:;()")) for i in word_ids]
    hits = []
    for k in range(len(words)):
        seq = [w for _, w in words[k:k + len(label)]]
        if [s.rstrip(".") for s in seq] == [s.rstrip(".") for s in label]:
            hits.append([i for i, _ in words[k:k + len(label)]])
    code = norm(option.get("code") or "")
    if code:
        hits += [[i] for i, w in words if w == code]
    return hits


def options_answer(ocr, schema, groups):
    circled = set(i for g in groups for i in g)
    questions = schema["questions"]
    counts = {}
    for q in questions:
        for t in {t.rstrip(".") for t in _tokens(q["text"])}:
            counts[t] = counts.get(t, 0) + 1
    weights = {t: 1.0 / c for t, c in counts.items()}
    anchors = {q["id"]: _anchor_line(ocr, q, weights) for q in questions}
    ys = sorted({ocr["lines"][a]["box"][1] for a in anchors.values() if a is not None})
    answers = {}
    for q in questions:
        a = anchors[q["id"]]
        if a is None or q.get("select") == "text":
            answers[q["id"]] = None
            continue
        top = ocr["lines"][a]["box"][1] - 4
        nxt = [y for y in ys if y > top + 6]
        bottom = nxt[0] - 4 if nxt else ocr["size"][1]
        area = [i for i, w in enumerate(ocr["words"]) if top <= (w["box"][1] + w["box"][3]) / 2 <= bottom]
        chosen = []
        for opt in q.get("options", []):
            if any(any(i in circled for i in hit) for hit in _option_hits(ocr, opt, area)):
                chosen.append(opt["label"])
        if q.get("select") == "many":
            answers[q["id"]] = chosen
        else:
            answers[q["id"]] = chosen[0] if len(chosen) == 1 else (chosen[0] if chosen else None)
    return {"answers": answers}


def answer(task, ocr, groups):
    if task["kind"] == "text":
        return text_answer(ocr, groups)
    return options_answer(ocr, task["schema"], groups)
