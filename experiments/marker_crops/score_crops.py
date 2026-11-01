"""Score run_crops.py output: per crop, does the answer name an answer-key item of that page?
exact = answer is the item (option code accepted); hit = item is contained in the answer."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from formeval import data

def norm(s):
    s = s.lower().replace("’", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"<[^>]+>|[*_#`|]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def strip_punct(s): return re.sub(r"[^\w%$]+", " ", s).strip()

def accepted(p):
    """list of acceptable-string sets, one per answer-key item"""
    t = data.load_truth(p)
    if t["kind"] == "text": return [{norm(i["text"])} for i in t["items"]]
    schema = json.loads((ROOT / "data/schemas" / f"{p}.json").read_text())
    opts = {}
    def walk(o):
        if isinstance(o, dict):
            if "id" in o and "options" in o: opts[o["id"]] = o["options"]
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(schema)
    acc = []
    for a in t["answers"]:
        if a["expected"] is None: continue
        s = {norm(a["expected"])}
        for o in opts.get(a["question_id"], []):
            if norm(o.get("label", "")) == norm(a["expected"]) and o.get("code"): s.add(norm(str(o["code"])))
        acc.append(s)
    return acc

for key in sys.argv[1:]:
    res = json.loads((ROOT / "experiments/marker_crops/out_vlm" / key / "results.json").read_text())
    print(f"===== {key} =====")
    for mode, rows in res.items():
        hit = exact = 0; misses = []
        by_page = {}
        for r in rows: by_page.setdefault(r["page"], []).append(r)
        for p, crops in by_page.items():
            acc = accepted(p); used = set()
            for r in crops:
                ans = norm(r["answer"]); ok = ex = False
                for i, s in enumerate(acc):
                    if i in used: continue
                    if any(strip_punct(ans) == strip_punct(x) for x in s): ok = ex = True
                    elif any(x in ans for x in s): ok = True
                    if ok: used.add(i); break
                hit += ok; exact += ex
                if not ok: misses.append(f"    {p} #{r['id']}: {r['answer'][:60]!r}  expected one of {sorted(acc)[0] if False else [sorted(s)[0] for s in acc]}")
        print(f"{mode:7s}: hit {hit}/{len(rows)}   exact {exact}/{len(rows)}   mean {sum(r['s'] for r in rows)/len(rows):.1f}s/crop")
        if misses: print("  misses:"); print("\n".join(misses))
