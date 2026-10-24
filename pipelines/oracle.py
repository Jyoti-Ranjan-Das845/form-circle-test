"""Cheating pipeline that reads the answer key. Use it to check the evaluator: it must score 100%."""
from formeval import data


def run(task):
    truth = data.load_truth(task["page_id"])
    if task["kind"] == "text":
        return {"marked": [{"text": i["text"], "context": " ".join(i.get("context_must_include", []))}
                           for i in truth["items"]]}
    return {"answers": {a["question_id"]: a["expected"] for a in truth["answers"]}}
