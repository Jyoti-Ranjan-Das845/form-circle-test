"""Image loading and saving. Pages are handled as RGB uint8 numpy arrays of shape (H, W, 3)."""
from pathlib import Path

import numpy as np
from PIL import Image


def load_rgb(path):
    """Read an image as RGB. Transparent areas are flattened onto white, so RGBA scans compare like paper."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    with Image.open(path) as im:
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            im = im.convert("RGBA")
            white = Image.new("RGBA", im.size, (255, 255, 255, 255))
            im = Image.alpha_composite(white, im)
        return np.array(im.convert("RGB"))


def save_rgb(array, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(array).save(path)
    return path


def upscale(image, factor):
    """Enlarge a PIL image; classic OCR engines read 20-40 px tall crops much better at 3x."""
    if factor == 1:
        return image
    return image.resize((image.width * factor, image.height * factor), Image.LANCZOS)
