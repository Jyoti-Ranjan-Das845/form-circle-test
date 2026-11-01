"""Both stages end to end with a stand-in reader (no model needed), plus dataset discovery and scoring."""
import json
import shutil

import pytest

from conftest import DATA
from markpipe import Reader, detect_pages, find_pairs, read_crops
from markpipe.dataset import PagePair


class EchoReader(Reader):
    """Answers with the crop's file name; fails on request."""
    name = "echo"

    def __init__(self, fail_on=None, max_images=2):
        self.fail_on, self.max_images, self.calls = fail_on, max_images, []

    def read(self, images, prompt):
        self.calls.append((list(images), prompt))
        if self.fail_on and self.fail_on in images[0].name:
            raise RuntimeError("boom")
        return images[0].name


def test_find_pairs():
    pairs = find_pairs(DATA)
    assert [p.page for p in pairs] == ["img_01", "img_02", "img_03", "img_04", "img_05", "img_06", "img_20"]
    assert find_pairs(DATA, ["img_20"])[0].clean.name == "img_20_unmarked.png"
    with pytest.raises(ValueError):
        find_pairs(DATA, ["img_99"])


def test_find_pairs_skips_orphans(tmp_path):
    shutil.copy(DATA / "img_01_marked.png", tmp_path / "img_01_marked.png")
    assert find_pairs(tmp_path) == []


def test_detect_and_read(tmp_path):
    results = detect_pages(find_pairs(DATA, ["img_01", "img_20"]), tmp_path)
    assert [(r.page, r.status, len(r.markers)) for r in results] == [("img_01", "ok", 4), ("img_20", "ok", 5)]
    meta = json.loads((tmp_path / "img_01" / "markers.json").read_text())
    assert all((tmp_path / "img_01" / m["crop_marked"]).exists() for m in meta["markers"])
    assert (tmp_path / "summary.json").exists()

    reader = EchoReader(fail_on="img_xx")
    out = read_crops(tmp_path, reader, ["marked", "both"])
    assert len(out["marked"]) == 9 and all(r["answer"].endswith("_marked.png") for r in out["marked"])
    assert all(len(images) == 2 for images, _ in reader.calls[9:])  # "both" sends two crops
    assert (tmp_path / "reads" / "echo" / "marked.json").exists()


def test_reader_errors_are_recorded_not_raised(tmp_path):
    detect_pages(find_pairs(DATA, ["img_01"]), tmp_path)
    rows = read_crops(tmp_path, EchoReader(fail_on="marker_02"), ["marked"])["marked"]
    assert [r["error"] is not None for r in rows] == [False, True, False, False]


def test_single_image_reader_skips_both(tmp_path):
    detect_pages(find_pairs(DATA, ["img_01"]), tmp_path)
    assert "both" not in read_crops(tmp_path, EchoReader(max_images=1), ["both"])


def test_bad_page_is_reported(tmp_path):
    pair = PagePair("broken", DATA / "img_01_marked.png", DATA / "img_20_unmarked.png")  # different sizes
    (result,) = detect_pages([pair], tmp_path)
    assert result.status == "error" and "sizes differ" in result.error


def test_read_without_detection_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_crops(tmp_path, EchoReader(), ["marked"])


def test_scoring():
    from score import load_key, score_rows
    key = {"p": {"items": [{"id": "a", "accept": ["Boston"]}, {"id": "b", "accept": ["YES", "1"]}]}}
    rows = [{"page": "p", "id": 1, "answer": "Boston U", "seconds": 1, "error": None},
            {"page": "p", "id": 2, "answer": "1", "seconds": 1, "error": None},
            {"page": "p", "id": 3, "answer": "NOTE", "seconds": 1, "error": None}]
    total = score_rows(rows, key)["total"]
    assert (total["hit"], total["exact"], total["extras"]) == (2, 1, 1)
    assert len(load_key()) == 7 and sum(len(v["items"]) for v in load_key().values()) == 38
