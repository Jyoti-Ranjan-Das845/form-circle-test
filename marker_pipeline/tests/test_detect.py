"""Detector behaviour on a real page, and on synthetic edits of it that cover the hard cases."""
import numpy as np
import pytest
from PIL import Image, ImageDraw

from markpipe import DetectorConfig, PageMismatchError, detect
from markpipe.crops import make_crops
from markpipe.imaging import load_rgb

RED, BLUE = (220, 40, 40), (40, 60, 220)


@pytest.fixture(scope="module")
def base(page01):
    clean, marked = page01
    _, markers = detect(clean, marked)
    return {m.id: m.box for m in markers}


def erase(clean, marked, box, start, end):
    """Put back clean pixels over a vertical slice [start, end) (fractions of the box width)."""
    out = marked.copy()
    x1, y1, x2, y2 = box
    xa, xb = int(x1 + (x2 - x1) * start), int(x1 + (x2 - x1) * end)
    out[y1:y2 + 1, xa:xb] = clean[y1:y2 + 1, xa:xb]
    return out


def draw(marked, fn):
    im = Image.fromarray(marked.copy())
    fn(ImageDraw.Draw(im))
    return np.array(im)


def test_real_page(page01):
    clean, marked = page01
    _, markers = detect(clean, marked)
    assert [m.shape for m in markers] == ["closed"] * 4
    assert all(m.red_fraction > 0.8 for m in markers)
    assert [m.id for m in markers] == [1, 2, 3, 4]


def test_identical_pages_have_no_marks(page01):
    clean, _ = page01
    _, markers = detect(clean, clean.copy())
    assert markers == []


def test_specks_are_ignored(page01):
    clean, _ = page01
    marked = clean.copy()
    marked[100:104, 100:104] = RED  # 16 px, under min_area
    assert detect(clean, marked)[1] == []


def test_size_mismatch_is_rejected(page01):
    clean, marked = page01
    with pytest.raises(PageMismatchError):
        detect(clean, marked[:-1])


def test_rgba_is_flattened_on_white(tmp_path):
    path = tmp_path / "a.png"
    Image.new("RGBA", (4, 4), (0, 0, 0, 0)).save(path)
    assert (load_rgb(path) == 255).all()


def test_small_gap_still_closed(page01, base):
    clean, marked = page01
    _, markers = detect(clean, erase(clean, marked, base[1], 0.45, 0.55))
    assert [m.shape for m in markers] == ["closed"] * 4


def test_large_missing_arc_is_open(page01, base):
    clean, marked = page01
    _, markers = detect(clean, erase(clean, marked, base[2], 0.0, 0.4))
    assert len(markers) == 4
    assert [m.shape for m in markers].count("open") == 1
    open_mark = next(m for m in markers if m.shape == "open")
    assert make_crops(open_mark, clean, marked).inside is None


def test_double_loop_is_one_mark(page01, base):
    clean, marked = page01
    x1, y1, x2, y2 = base[3]
    edited = draw(marked, lambda d: d.ellipse([x1 - 7, y1 - 7, x2 + 7, y2 + 7], outline=RED, width=2))
    _, markers = detect(clean, edited)
    assert len(markers) == 4
    assert sum(m.note.startswith("double stroke") for m in markers) == 1


def test_touching_circles_are_split(page01):
    clean, marked = page01
    edited = draw(marked, lambda d: (d.ellipse([60, 650, 150, 690], outline=RED, width=2),
                                     d.ellipse([148, 650, 240, 690], outline=RED, width=2)))
    _, markers = detect(clean, edited)
    assert len(markers) == 6
    split = [m for m in markers if m.note.startswith("split")]
    assert len(split) == 2 and all(m.shape == "closed" for m in split)


def test_tick_is_open(page01):
    clean, marked = page01
    _, markers = detect(clean, draw(marked, lambda d: d.line([(300, 700), (312, 718), (340, 690)], fill=RED, width=3)))
    assert len(markers) == 5
    assert [m.shape for m in markers].count("open") == 1


def test_any_ink_colour_is_found(page01):
    clean, marked = page01
    _, markers = detect(clean, draw(marked, lambda d: d.ellipse([400, 500, 480, 530], outline=BLUE, width=2)))
    assert len(markers) == 5
    assert min(m.red_fraction for m in markers) < 0.1


def test_inside_crop_keeps_only_the_interior(page01):
    clean, marked = page01
    cfg = DetectorConfig()
    _, markers = detect(clean, marked, cfg)
    cut = make_crops(markers[0], clean, marked, cfg)
    assert cut.inside is not None and cut.inside.shape == cut.clean.shape
    assert (cut.inside[0] == 255).all() and (cut.inside[-1] == 255).all()  # outside the circle is whitened
    assert (cut.inside < 128).any()  # the circled text survives


def test_mark_at_page_edge(page01):
    clean, _ = page01
    marked = draw(clean, lambda d: d.ellipse([0, 0, 60, 30], outline=RED, width=2))
    _, markers = detect(clean, marked)
    assert len(markers) == 1
    cut = make_crops(markers[0], clean, marked)
    assert cut.box[0] == 0 and cut.box[1] == 0
