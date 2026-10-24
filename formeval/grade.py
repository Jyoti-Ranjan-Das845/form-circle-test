"""Grade one page of pipeline output against the answer key.

Score for a page = correct / (items in the key + extra things the pipeline reported that are not in the key).
Overall accuracy is the same fraction summed over all pages.
"""
from .normalize import norm, same_text, words


def _context_ok(item, context):
    """For repeated words: the reported line must contain the anchor words (and none of the excluded ones)."""
    need = [norm(w) for w in item.get("context_must_include", [])]
    avoid = [norm(w) for w in item.get("context_must_exclude", [])]
    if not need and not avoid:
        return True
    got = words(context or "")
    return all(w in got for w in need) and not any(w in got for w in avoid)


def grade_text(truth, output):
    preds = list(output.get("marked", []))
    used = [False] * len(preds)
    results = []
    for item in truth["items"]:
        hit = None
        for i, p in enumerate(preds):
            if not used[i] and same_text(p["text"], item["text"]) and _context_ok(item, p.get("context")):
                hit = i
                break
        if hit is not None:
            used[hit] = True
        results.append({"id": item["id"], "expected": item["text"], "got": preds[hit]["text"] if hit is not None else None,
                        "correct": hit is not None, "case_type": item["case_type"]})
    extras = [p["text"] for p, u in zip(preds, used) if not u]
    return results, extras


def _resolve(answer, question):
    """Map an answer (label or code) to the schema's option label. Unknown answers are kept as-is."""
    if answer is None:
        return None
    for opt in question.get("options", []):
        if same_text(answer, opt["label"]) or (opt.get("code") and norm(answer) == norm(opt["code"])):
            return opt["label"]
    return answer


def _answer_ok(expected, got, question):
    select = question.get("select", "one")
    if select == "many":
        exp = {norm(x) for x in (expected or [])}
        got = {norm(_resolve(x, question)) for x in (got or [])}
        return exp == got
    if expected is None:
        return got is None or norm(got) == ""
    if select == "text":
        return same_text(expected, got or "")
    return got is not None and same_text(expected, _resolve(got, question))


def grade_options(truth, schema, output):
    questions = {q["id"]: q for q in schema["questions"]}
    answers = output.get("answers", {})
    results = []
    for a in truth["answers"]:
        got = answers.get(a["question_id"])
        results.append({"id": a["id"], "expected": a["expected"], "got": got,
                        "correct": _answer_ok(a["expected"], got, questions[a["question_id"]]),
                        "case_type": a["case_type"]})
    return results, []  # options pages have a fixed set of questions, so there are no extras


def grade_page(truth, schema, output):
    if truth["kind"] == "text":
        results, extras = grade_text(truth, output)
    else:
        results, extras = grade_options(truth, schema, output)
    correct = sum(r["correct"] for r in results)
    total = len(results) + len(extras)
    return {"page_id": truth["page_id"], "kind": truth["kind"], "correct": correct, "items": len(results),
            "extras": extras, "accuracy": correct / total if total else 1.0, "results": results}
