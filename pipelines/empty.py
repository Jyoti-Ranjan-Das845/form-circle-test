"""Baseline that never finds anything. Text pages score 0%; options pages score only their blank questions."""


def run(task):
    if task["kind"] == "text":
        return {"marked": []}
    return {"answers": {q["id"]: None for q in task["schema"]["questions"]}}
