"""Copy this file to start a new pipeline, then run:

    python -m formeval.run --pipeline pipelines/my_pipeline.py

See formeval/contract.py for the full input/output contract.
"""


def run(task):
    image_path = task["image_path"]   # the page to read
    instruction = task["instruction"]  # what to return, in plain English (good as an LLM prompt)

    if task["kind"] == "text":
        # Find every circled piece of printed text.
        marked = []  # e.g. [{"text": "smoking", "context": "the period when smoking was banned on"}]
        return {"marked": marked}

    # Options page: answer every question in the schema.
    answers = {}
    for q in task["schema"]["questions"]:
        # q = {"id": "q1", "text": "...", "select": "one" | "many" | "text", "options": [{"label": "YES"}, ...]}
        answers[q["id"]] = None  # a label, a list of labels for "many", or None when nothing is circled
    return {"answers": answers}
