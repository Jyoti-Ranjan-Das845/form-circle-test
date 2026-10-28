"""Send the marked colour pages to a document parser on OpenDocRouter and save the raw responses.

No prompt can be passed: each model runs its own fixed recipe. The only switches are the model and `layout`.
Needs OPEN_DOC_ROUTER_API_KEY in .env (project root).

    .venv_vlm/bin/python experiments/opendocrouter/parse.py --model llamaindex/ocria-1 [--layout] [--pages 04,20]
Responses land in experiments/opendocrouter/out/<model>/<layout|plain>/<page>.json
"""
import argparse
import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URL = "https://www.opendocrouter.ai/v1/parse"
PAGES = ["01", "02", "03", "04", "05", "06", "20"]


def _key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.strip().startswith("OPEN_DOC_ROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if key:
                return key
    raise SystemExit("OPEN_DOC_ROUTER_API_KEY is empty in .env")


def parse(image, model, layout, retries=5):
    body = {"model": model, "layout": layout,
            "document": {"data": base64.b64encode(image.read_bytes()).decode(), "mime_type": "image/png"}}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < retries - 1:  # rate limit / model starting
                time.sleep(int(e.headers.get("Retry-After") or 30))
                continue
            raise SystemExit(f"HTTP {e.code}: {e.read()[:300]!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="llamaindex/ocria-1")
    ap.add_argument("--layout", action="store_true")
    ap.add_argument("--pages", default=",".join(PAGES))
    ap.add_argument("--clean", action="store_true", help="send the unmarked originals instead")
    args = ap.parse_args()
    mode = ("layout" if args.layout else "plain") + ("-clean" if args.clean else "")
    out = Path(__file__).parent / "out" / args.model.replace("/", "__") / mode
    out.mkdir(parents=True, exist_ok=True)
    for pid in args.pages.split(","):
        image = next((ROOT / ("real_forms" if args.clean else "real_forms_marked")).glob(f"{pid}_*.png"))
        t = time.time()
        res = parse(image, args.model, args.layout)
        (out / f"{pid}.json").write_text(json.dumps(res, indent=1))
        pages = res.get("pages", [])
        status = pages[0].get("status") if pages else res.get("status")
        print(f"page {pid}  {status}  ${res.get('charge_usd', 0):.4f}  {time.time() - t:.1f}s")


if __name__ == "__main__":
    main()
