import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiment"))

DATA = ROOT / "experiment" / "dataset" / "ready_to_use"


@pytest.fixture(scope="session")
def page01():
    """(clean, marked) arrays of a real page with four red circles."""
    from markpipe.imaging import load_rgb
    return load_rgb(DATA / "img_01_unmarked.png"), load_rgb(DATA / "img_01_marked.png")
