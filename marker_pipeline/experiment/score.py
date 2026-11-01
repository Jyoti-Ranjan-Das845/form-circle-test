"""Score reader answers against answer_key.json.

Per page, each crop's answer is matched to at most one answer-key item, exact matches first:
    exact  the answer is the item (case, spacing and punctuation ignored)
    hit    the item appears in the answer as whole words (e.g. "Boston U" for "Boston")
A crop whose answer matches no item is an extra; an item no crop matched is missed.
"""
import json
import re
from pathlib import Path

KEY = Path(__file__).resolve().parent / "answer_key.json"


def norm(text):
    text = (text or "").lower().replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def bare(text):
    """Letters, digits, % and $ only, single-spaced."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w%$]+", " ", norm(text))).strip()


def _contains(answer, item):
    item = bare(item)
    return bool(item) and re.search(rf"(?<!\w){re.escape(item)}(?!\w)", bare(answer)) is not None


def load_key(path=KEY):
    return {k: v for k, v in json.loads(Path(path).read_text()).items() if not k.startswith("_")}


def score_page(rows, page_key):
    """rows: [{"id", "answer", "error"}] for one page and mode."""
    items = page_key["items"]
    open_items = list(range(len(items)))
    matched = {}  # row index -> (item index, "exact" | "hit")
    for kind, test in (("exact", lambda a, x: bare(a) == bare(x)), ("hit", _contains)):
        for r, row in enumerate(rows):
            if r in matched or not row.get("answer"):
                continue
            for i in open_items:
                if any(test(row["answer"], acc) for acc in items[i]["accept"]):
                    matched[r] = (i, kind)
                    open_items.remove(i)
                    break
    return {
        "items": len(items), "crops": len(rows),
        "exact": sum(k == "exact" for _, k in matched.values()),
        "hit": len(matched),
        "missed": [items[i]["id"] for i in open_items],
        "extras": [rows[r]["answer"] for r in range(len(rows)) if r not in matched and rows[r].get("answer")],
        "errors": [f"#{row['id']}: {row['error']}" for row in rows if row.get("error")],
    }


def score_rows(rows, key=None):
    """All pages of one reader + mode. Pages missing from the run count all their items as missed."""
    key = key or load_key()
    by_page = {}
    for row in rows:
        by_page.setdefault(row["page"], []).append(row)
    pages = {p: score_page(by_page.get(p, []), key[p]) for p in key}
    total = {k: sum(v[k] for v in pages.values()) for k in ("items", "crops", "exact", "hit")}
    total["extras"] = sum(len(v["extras"]) for v in pages.values())
    total["errors"] = sum(len(v["errors"]) for v in pages.values())
    secs = [r["seconds"] for r in rows if r.get("answer") is not None]
    total["s_per_crop"] = round(sum(secs) / len(secs), 2) if secs else None
    return {"total": total, "pages": pages}


def score_detection(summary, key=None):
    """Marks found per page vs items in the answer key."""
    key = key or load_key()
    found = {s["page"]: s.get("markers", 0) for s in summary}
    return {p: {"marks": found.get(p, 0), "items": len(v["items"])} for p, v in key.items()}
