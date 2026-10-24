"""Load pages, schemas and answer keys, and find which pages have been marked."""
import json
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR = ROOT / "real_forms"
MARKED_DIR = ROOT / "real_forms_marked"
DATA_DIR = ROOT / "data"


def load_truth(page_id):
    return json.loads((DATA_DIR / "ground_truth" / f"{page_id}.json").read_text())


def load_schema(page_id):
    path = DATA_DIR / "schemas" / f"{page_id}.json"
    return json.loads(path.read_text()) if path.exists() else None


def all_page_ids():
    return sorted(p.stem for p in (DATA_DIR / "ground_truth").glob("*.json"))


def is_marked(page_id, marked_dir=MARKED_DIR):
    """A page counts as ready once its marked copy differs from the clean original."""
    name = load_truth(page_id)["image"]
    marked = Path(marked_dir) / name
    if not marked.exists():
        return False
    a = Image.open(CLEAN_DIR / name).convert("L")
    b = Image.open(marked).convert("L")
    if a.size != b.size:
        return True
    return ImageChops.difference(a, b).getbbox() is not None
