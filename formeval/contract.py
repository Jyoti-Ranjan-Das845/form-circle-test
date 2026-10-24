"""The contract between the evaluator and a pipeline.

A pipeline is any Python function `run(task) -> dict`. The evaluator calls it once per page.

Input `task` (a dict):
    page_id      "01" ... "20"
    image_path   absolute path to the page image (PNG)
    kind         "text" or "options"
    instruction  plain-English description of what to return (same for every pipeline)
    schema       options pages only: {"questions": [...]} — see data/schemas/*.json; None for text pages

Output for kind == "text":
    {"marked": [{"text": "smoking", "context": "the period when smoking was banned on"}, ...]}
    - text:    the circled printed text, exactly as printed
    - context: the full printed line the text sits on (used to tell repeated words apart)

Output for kind == "options":
    {"answers": {"q1": "YES", "q2": ["Coffee", "Mouth wash"], "q3": null, ...}}
    - one entry per question id in the schema
    - select "one":  an option label (or its code), or null if nothing is marked
    - select "many": a list of option labels (or codes); [] or null if nothing is marked
    - select "text": the marked/written text, or null

The pipeline never sees the answer key.
"""

TEXT_INSTRUCTION = (
    "This is a scanned document page. Some printed words or phrases have been circled by hand. "
    "Return every piece of printed text that is circled, exactly as printed, together with the full "
    "printed line it appears on. Do not return anything that is not circled. "
    'Return JSON: {"marked": [{"text": "...", "context": "..."}]}'
)

OPTIONS_INSTRUCTION = (
    "This is a scanned questionnaire page. A person has circled their choices by hand. "
    "For each question in the schema, return the option(s) that are circled, using the option labels "
    "from the schema. Use null when nothing is circled for a question. "
    'Return JSON: {"answers": {"<question id>": "<label>" | ["<label>", ...] | null}}'
)


class ContractError(ValueError):
    """The pipeline returned something that does not follow the contract."""


def validate(task, output):
    """Check a pipeline's output shape. Raises ContractError with a readable message."""
    if not isinstance(output, dict):
        raise ContractError(f"pipeline must return a dict, got {type(output).__name__}")
    if task["kind"] == "text":
        marked = output.get("marked")
        if not isinstance(marked, list):
            raise ContractError('text pages must return {"marked": [...]}')
        for i, m in enumerate(marked):
            if not isinstance(m, dict) or not isinstance(m.get("text"), str):
                raise ContractError(f'marked[{i}] must be {{"text": str, "context": str}}')
            if m.get("context") is not None and not isinstance(m["context"], str):
                raise ContractError(f"marked[{i}].context must be a string")
    else:
        answers = output.get("answers")
        if not isinstance(answers, dict):
            raise ContractError('options pages must return {"answers": {...}}')
        for qid, a in answers.items():
            if a is not None and not isinstance(a, (str, list)):
                raise ContractError(f"answers[{qid!r}] must be a string, a list or null")
            if isinstance(a, list) and not all(isinstance(x, str) for x in a):
                raise ContractError(f"answers[{qid!r}] list must contain strings")
