#!/usr/bin/env python3
"""Score parrotlet prescription JSON against the human reading in eval/ground_truth.json.

    python prescription_ocr/eval/score.py prescription_ocr/results/mlx

Writes SCORES.md and scores.csv into that results folder. Standard library only.

What is scored, per page (only readings marked sure=true count toward exact matches):
  BP        systolic and diastolic, exact
  date      document date, exact (pages with a legible date)
  labs      name + value both right; "mislabelled" = right value under the wrong name; extra = value on no GT row
  meds      line found (fuzzy name match), name exact, name CER (character error rate), times per day, duration
            ("none" on the page and a duration in the output = invented duration)
  tests     advised tests found
  invented  vitals that are not on the page (anything except BP), lab rows with no source, medicine lines with no
            source, durations not on the page
"""

import csv
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).resolve().parent
GT = json.loads((HERE / "ground_truth.json").read_text())

LAB_ALIASES = {
    "FBS": ["fbs", "fastingbloodsugar", "fbg", "fpg", "fastingglucose"],
    "PPBS": ["ppbs", "2hrppbs", "2hppbs", "ppbg", "pp", "postprandial"],
    "HbA1c": ["hba1c", "a1c", "glycatedhb", "glycatedhaemoglobin", "glycosylatedhaemoglobin"],
    "TSH": ["tsh"],
    "creatinine": ["creatinine", "creat", "screatinine", "screat", "serumcreatinine"],
    "Na": ["na", "sodium", "sna", "serumsodium"],
    "K": ["k", "potassium", "sk", "serumpotassium"],
    "LDL": ["ldl", "ldlc", "ldlcholesterol"],
    "TG": ["tg", "triglycerides", "triglyceride"],
    "Hb": ["hb", "haemoglobin", "hemoglobin"],
    "AST/ALT": ["astalt", "sgotsgpt"],
}
TEST_KEYS = {
    "USG": ["usg", "ultrasound", "sonography"], "creatinine": ["creat"], "lipid": ["lipid"], "FBS": ["fbs", "fasting"],
    "PPBS": ["ppbs", "pp"], "urea": ["urea"], "AST": ["ast", "sgot", "lft", "liver"], "Hb": ["hb"], "TSH": ["tsh"],
    "Na": ["na", "sodium"], "K": ["k", "potassium"],
}


def compact(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def canon_lab(name: str):
    c = compact(name)
    for k, al in LAB_ALIASES.items():
        if c in al:
            return k
    return None


def med_key(name: str) -> str:
    s = re.sub(r"^\s*(tab|cap|inj|syp|oint|gel)\b\.?", "", name.strip(), flags=re.I)
    return compact(s)


def cer(ref: str, hyp: str) -> float:
    a, b = med_key(ref), med_key(hyp)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / max(len(a), 1)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return str(v).strip()


def same(a, b) -> bool:
    a, b = num(a), num(b)
    if isinstance(a, float) and isinstance(b, float):
        return abs(a - b) < 1e-6
    return str(a) == str(b)


def per_day(freq):
    if not freq:
        return None
    f = str(freq).lower().strip()
    if "week" in f:
        return "weekly"
    if re.fullmatch(r"[\d½.]+(-[\d½.]+){2,3}", f):
        return sum(1 for x in f.split("-") if x not in ("0", ""))
    return {"od": 1, "hs": 1, "bd": 2, "bid": 2, "tds": 3, "tid": 3, "qid": 4}.get(f)


def duration(d):
    if not d:
        return "none"
    v, u = d.get("value"), str(d.get("unit", "")).lower().rstrip("s")
    v = int(v) if isinstance(v, float) and v.is_integer() else v
    return f"{v} {u}s"


def norm_dur(s):
    return s if s in (None, "none") else re.sub(r"(day|month|week)s?$", r"\1s", s)


def match_meds(gt, out):
    """Align the two medicine lists in order (both follow the page top to bottom), maximising name similarity.
    A pair counts only if its names are at least 25% similar; lines can be skipped on either side."""
    sim = [[SequenceMatcher(None, med_key(g["name"]), med_key(o.get("name", ""))).ratio() for o in out] for g in gt]
    n, k = len(gt), len(out)
    dp = [[0.0] * (k + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, k + 1):
            pair = dp[i - 1][j - 1] + sim[i - 1][j - 1] if sim[i - 1][j - 1] >= 0.25 else -1
            dp[i][j] = max(dp[i - 1][j], dp[i][j - 1], pair)
    m, i, j = {}, n, k
    while i and j:
        s = sim[i - 1][j - 1]
        if s >= 0.25 and abs(dp[i][j] - (dp[i - 1][j - 1] + s)) < 1e-9:
            m[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif dp[i][j] == dp[i - 1][j]:
            i -= 1
        else:
            j -= 1
    return m


def score_page(page: str, out):
    g = GT[page]
    r = {"page": page, "valid_json": out is not None}
    pe = (out or {}).get("prescription_elements", {}) if isinstance(out, dict) else {}
    notes = []

    # BP and other vitals
    obs = pe.get("observations", []) or []
    sys_ = next((o.get("value") for o in obs if o.get("name") == "SystolicBP"), None)
    dia = next((o.get("value") for o in obs if o.get("name") == "DiastolicBP"), None)
    r["bp_ok"] = int(same(sys_, g["bp"][0])) + int(same(dia, g["bp"][1]))
    r["bp_n"] = 2
    bad_vitals = [f"{o.get('name')} {o.get('value')}" for o in obs
                  if o.get("category") == "vital-sign" and o.get("name") not in ("SystolicBP", "DiastolicBP")]
    if bad_vitals:
        notes.append("vitals not on page: " + ", ".join(bad_vitals))

    # date
    r["date_n"] = int(g["date"] is not None)
    r["date_ok"] = int(g["date"] is not None and pe.get("documentDate") == g["date"])

    # labs
    rows = []
    for d in pe.get("diagnosticResults", []) or []:
        for x in d.get("results", []) or [{"name": d.get("name"), "value": d.get("value")}]:
            rows.append((x.get("name") or d.get("name") or "", x.get("value")))
    sure_labs = [l for l in g["labs"] if l["sure"]]
    r["labs_n"], r["labs_ok"], r["labs_mislabelled"] = len(sure_labs), 0, 0
    for l in sure_labs:
        hits = [n for n, v in rows if same(v, l["value"])]
        if any(canon_lab(n) == l["name"] for n in hits):
            r["labs_ok"] += 1
        elif hits:
            r["labs_mislabelled"] += 1
            notes.append(f"{l['name']} {l['value']} labelled '{hits[0]}'")
    unsure = {l["name"] for l in g["labs"] if not l["sure"]}  # a disputed reading is not counted as invented
    extra = [f"{n} {v}" for n, v in rows
             if not any(same(v, l["value"]) for l in g["labs"]) and canon_lab(n) not in unsure]
    r["labs_extra"] = len(extra)
    if extra:
        notes.append("lab values not on page: " + ", ".join(extra))

    # medicines
    meds = pe.get("medicationRequest", []) or []
    m = match_meds(g["meds"], meds)
    r["meds_n"], r["meds_found"], r["meds_extra"] = len(g["meds"]), len(m), len(meds) - len(m)
    sure_found = [i for i in m if g["meds"][i]["sure"]]
    r["names_n"] = sum(1 for x in g["meds"] if x["sure"])
    r["names_exact"] = sum(1 for i in sure_found if med_key(g["meds"][i]["name"]) == med_key(meds[m[i]]["name"]))
    cers = [cer(g["meds"][i]["name"], meds[m[i]]["name"]) for i in sure_found]
    r["name_cer"] = round(sum(cers) / len(cers), 2) if cers else None
    r["freq_n"] = r["freq_ok"] = r["dur_n"] = r["dur_ok"] = r["dur_invented"] = 0
    for i, gm in enumerate(g["meds"]):
        o = meds[m[i]] if i in m else None
        if gm["per_day"] is not None:
            r["freq_n"] += 1
            r["freq_ok"] += int(o is not None and per_day(o.get("frequency")) == gm["per_day"])
        if gm["duration"] is not None:
            r["dur_n"] += 1
            got = norm_dur(duration(o.get("duration"))) if o else None
            r["dur_ok"] += int(got == norm_dur(gm["duration"]))
            r["dur_invented"] += int(gm["duration"] == "none" and got not in (None, "none"))
    unmatched = [x["name"] for i, x in enumerate(g["meds"]) if i not in m]
    if unmatched:
        notes.append("medicines missed: " + ", ".join(unmatched))
    r["med_map"] = "; ".join(f"{g['meds'][i]['name']} → {meds[j]['name']}" for i, j in sorted(m.items()))

    # advised tests
    names = " ".join(compact(s.get("name", "")) for s in pe.get("serviceRequest", []) or [])
    r["tests_n"] = len(g["tests"])
    r["tests_ok"] = sum(1 for t in g["tests"] if any(k in names for k in TEST_KEYS[t]))

    r["invented"] = len(bad_vitals) + r["labs_extra"] + r["meds_extra"] + r["dur_invented"]
    r["notes"] = " · ".join(notes)
    return r


def pct(a, b):
    return f"{a}/{b} ({round(100 * a / b)}%)" if b else "–"


def main():
    res_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "results" / "mlx"
    files = sorted(p for p in res_dir.glob("rx*.json"))
    rows = []
    for f in files:
        page = f.stem.split("_")[0]
        r = score_page(page, json.loads(f.read_text()).get("json"))
        r["run"] = f.stem
        rows.append(r)

    fields = ["run", "valid_json", "bp_ok", "bp_n", "date_ok", "date_n", "labs_ok", "labs_mislabelled", "labs_n",
              "labs_extra", "meds_found", "meds_n", "meds_extra", "names_exact", "names_n", "name_cer", "freq_ok",
              "freq_n", "dur_ok", "dur_n", "dur_invented", "tests_ok", "tests_n", "invented", "med_map", "notes"]
    with open(res_dir / "scores.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    main_rows = [r for r in rows if r["run"] == r["page"]]
    T = lambda k: sum(r[k] for r in main_rows)
    cer_all = [r["name_cer"] for r in main_rows if r["name_cer"] is not None]

    L = ["# Scores: parrotlet-v-2.5-pro vs human reading", "",
         f"Results: `{res_dir.name}/` · ground truth: `eval/ground_truth.json` (the README readings; not verified by "
         "the prescriber). Regenerate with `python prescription_ocr/eval/score.py prescription_ocr/results/"
         f"{res_dir.name}`.", "",
         "Exact-match scores use only readings the human was sure of. **Name CER** = character error rate on "
         "medicine names (0 = exact, 1 = nothing right). **Meds found** = an output line aligned to that page line "
         "(in order, names at least 25% alike); its name can still be wrong. **Invented** = vitals, lab rows, medicine lines and "
         "durations in the output that are not on the page.", "",
         "## Per page", "",
         "| run | JSON | BP | date | labs right | labs mislabelled | meds found | names exact | name CER | "
         "times/day | duration | tests | invented |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['run']} | {'ok' if r['valid_json'] else '**invalid**'} | {r['bp_ok']}/2 | "
                 f"{r['date_ok']}/{r['date_n'] or '–'} | {r['labs_ok']}/{r['labs_n']} | {r['labs_mislabelled']} | "
                 f"{r['meds_found']}/{r['meds_n']} | {r['names_exact']}/{r['names_n']} | "
                 f"{r['name_cer'] if r['name_cer'] is not None else '–'} | {r['freq_ok']}/{r['freq_n']} | "
                 f"{r['dur_ok']}/{r['dur_n']} | {r['tests_ok']}/{r['tests_n']} | {r['invented']} |")
    L += ["", "Rows with a suffix are reruns (repetition penalty 1.1) and are not in the totals below.", "",
          "## Totals, plain runs rx1–rx8", "",
          "| field | right | |", "|---|---|---|",
          f"| BP values | {pct(T('bp_ok'), T('bp_n'))} | |",
          f"| document date | {pct(T('date_ok'), T('date_n'))} | |",
          f"| lab name + value | {pct(T('labs_ok'), T('labs_n'))} | {T('labs_mislabelled')} more had the right value "
          "under the wrong name |",
          f"| medicine lines found | {pct(T('meds_found'), T('meds_n'))} | |",
          f"| medicine name exact | {pct(T('names_exact'), T('names_n'))} | mean name CER "
          f"{round(sum(cer_all) / len(cer_all), 2) if cer_all else '–'} |",
          f"| times per day | {pct(T('freq_ok'), T('freq_n'))} | |",
          f"| duration | {pct(T('dur_ok'), T('dur_n'))} | {T('dur_invented')} durations not on the page |",
          f"| advised tests | {pct(T('tests_ok'), T('tests_n'))} | |",
          f"| invented items | {T('invented')} | vitals, lab rows, medicine lines, durations |", "",
          "## How each medicine line was matched, and what went wrong", ""]
    for r in rows:
        L.append(f"**{r['run']}**: {r['med_map'] or 'no medicines in output'}")
        if r["notes"]:
            L.append(f"  \n_{r['notes']}_")
        L.append("")
    (res_dir / "SCORES.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
