"""Synthetic edge cases for extract_markers.detect(): modify page 01's marked copy and check what comes out.
Cases: small stroke gap, large missing arc, double loop at larger radius, two touching circles, tick,
blue ink. Writes overlays to experiments/marker_crops/out_edge_cases/."""
import sys, json, argparse
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_markers as em

clean = em.load_rgb(em.CLEAN / "01_text_typed_report_airliner_air_study.png")
marked0 = em.load_rgb(em.MARKED / "01_text_typed_report_airliner_air_study.png")
a = argparse.Namespace(gap=8, pad=6, min_area=40, diff_thresh=30)
_, base = em.detect(clean, marked0, a)
print("base page 01:", [(m["id"], m["shape"]) for m in base])
OUT = Path(__file__).resolve().parent / "out_edge_cases"; OUT.mkdir(exist_ok=True)

def erase(marked, box, frac_from, frac_to, axis="x"):
    """set the ink inside a horizontal slice of the marker box back to clean pixels"""
    m = marked.copy(); x1, y1, x2, y2 = box
    if axis == "x": xa, xb = int(x1 + (x2 - x1) * frac_from), int(x1 + (x2 - x1) * frac_to); m[y1:y2 + 1, xa:xb] = clean[y1:y2 + 1, xa:xb]
    else:           ya, yb = int(y1 + (y2 - y1) * frac_from), int(y1 + (y2 - y1) * frac_to); m[ya:yb, x1:x2 + 1] = clean[ya:yb, x1:x2 + 1]
    return m

def draw(marked, fn):
    im = Image.fromarray(marked.copy()); fn(ImageDraw.Draw(im)); return np.array(im)

b = {m["id"]: (m["x1"], m["y1"], m["x2"], m["y2"]) for m in base}
RED, BLUE = (220, 40, 40), (40, 60, 220)
cases = {
 "gap_10px_top":      erase(marked0, b[1], 0.45, 0.55, "x"),                  # ~10 px gap in top & bottom of circle 1 -> still 1 closed
 "arc_40pct_missing": erase(marked0, b[2], 0.0, 0.4, "x"),                    # left 40% of circle 2 gone -> open
 "double_loop":       draw(marked0, lambda d: d.ellipse([b[3][0]-7, b[3][1]-7, b[3][2]+7, b[3][3]+7], outline=RED, width=2)),
 "touching_pair":     draw(marked0, lambda d: (d.ellipse([60, 650, 150, 690], outline=RED, width=2), d.ellipse([148, 650, 240, 690], outline=RED, width=2))),
 "tick":              draw(marked0, lambda d: d.line([(300, 700), (312, 718), (340, 690)], fill=RED, width=3)),
 "blue_circle":       draw(marked0, lambda d: d.ellipse([400, 500, 480, 530], outline=BLUE, width=2)),
}
expect = {"gap_10px_top": "4 markers, all closed", "arc_40pct_missing": "4 markers, #2 open",
          "double_loop": "4 markers, #3 closed with 'double stroke' note", "touching_pair": "6 markers, two 'split' notes",
          "tick": "5 markers, one open", "blue_circle": "5 markers, one with red_fraction ~0"}
for name, mk in cases.items():
    ink, ms = em.detect(clean, mk, a)
    ov = Image.fromarray(mk.copy()); d = ImageDraw.Draw(ov)
    for m in ms:
        col = (0, 160, 0) if m["shape"] == "closed" else (255, 140, 0)
        d.rectangle([m["x1"] - 4, m["y1"] - 4, m["x2"] + 4, m["y2"] + 4], outline=col, width=2); d.text((m["x1"], m["y1"] - 12), str(m["id"]), fill=col)
    ov.save(OUT / f"{name}.png")
    inside = sum(1 for i in em.INTERIORS if i.any())
    print(f"\n{name}: expected {expect[name]}")
    for m in ms:
        print(f"   #{m['id']} {m['shape']:6s} box=({m['x1']},{m['y1']})-({m['x2']},{m['y2']}) ink={m['ink_px']} red={m['red_fraction']} {m['note']}")
    print(f"   inside-only interiors available: {inside}/{len(ms)}")
