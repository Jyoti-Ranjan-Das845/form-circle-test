"""Send the 7 marked pages to a local Ollama model with the same short prompts used in the manual tests.

Usage:  python3 experiments/ollama_manual.py qwen3-vl:2b-instruct
Saves the raw answers to experiments/ollama/<model>/<page>.txt and prints them with timings.
"""
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = "Can you identify which words are circled in red in the image?"
FORM = "The right answer to each question is marked with a red circle. Which answers are circled?"
PAGES = {
    "01": ("01_text_typed_report_airliner_air_study.png", TEXT),
    "02": ("02_text_typed_lab_report.png", TEXT),
    "03": ("03_text_article_serif_with_italics.png", TEXT),
    "04": ("04_text_two_column_journal_page.png", TEXT),
    "05": ("05_text_memo_serif_with_bullets.png", TEXT),
    "06": ("06_text_memo_key_findings_bullets.png", TEXT),
    "20": ("20_options_health_survey_yes_no_circle.png", FORM),
}


def ask(model, image, prompt):
    body = {"model": model, "stream": False,
            "messages": [{"role": "user", "content": prompt,
                          "images": [base64.b64encode(image.read_bytes()).decode()]}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"]


def main():
    model = sys.argv[1]
    out = ROOT / "experiments" / "ollama" / model.replace(":", "_")
    out.mkdir(parents=True, exist_ok=True)
    for pid, (name, prompt) in PAGES.items():
        t = time.perf_counter()
        answer = ask(model, ROOT / "real_forms_marked" / name, prompt)
        secs = time.perf_counter() - t
        (out / f"{pid}.txt").write_text(f"prompt: {prompt}\nseconds: {secs:.1f}\n\n{answer}\n")
        print(f"===== page {pid}  ({secs:.1f}s)\n{answer.strip()}\n")


if __name__ == "__main__":
    main()
