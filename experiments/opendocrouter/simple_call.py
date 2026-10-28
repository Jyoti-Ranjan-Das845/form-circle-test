# pip install opendocrouter
import base64

from opendocrouter import OpenDocRouter

FILE = "real_forms_marked/20_options_health_survey_yes_no_circle.png"

client = OpenDocRouter()  # reads OPEN_DOC_ROUTER_API_KEY

result = client.parse.create(
    model="llamaindex/ocria-1",
    document={"data": base64.b64encode(open(FILE, "rb").read()).decode(), "mime_type": "image/png"},
    layout=True,
)

for page in result.pages:
    if page.status == "error":
        print(f"Page {page.page} failed: {page.error.code}")

markdown = "\n\n".join(p.markdown or "" for p in result.pages if p.status == "ok")
print(markdown)
