"""Classic OCR engines. They read everything in the crop and take no instruction, so the fair input for them is
the `inside` crop (only the circled text). Crops are upscaled first: engines are tuned for ~30 px tall letters."""
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from ..imaging import upscale
from .base import Reader, ReaderError


class RapidOCRReader(Reader):
    """PP-OCR detection + recognition models through ONNX Runtime (the PaddleOCR family, no Paddle install)."""
    name = "rapidocr"
    follows_instructions = False

    def __init__(self, scale=3):
        self.scale = scale
        try:
            from rapidocr import RapidOCR
            self._engine, self._new_api = RapidOCR(params={"Global.log_level": "error"}), True
        except ImportError:
            try:
                from rapidocr_onnxruntime import RapidOCR
                self._engine, self._new_api = RapidOCR(), False
            except ImportError as e:
                raise ReaderError("RapidOCR is not installed (pip install rapidocr onnxruntime)") from e

    def read(self, images, prompt=None):
        if len(images) != 1:
            raise ReaderError("rapidocr reads one image at a time")
        with Image.open(images[0]) as im:
            arr = np.array(upscale(im.convert("RGB"), self.scale))
        if self._new_api:
            out = self._engine(arr)
            return " ".join(out.txts or ()).strip()
        result, _ = self._engine(arr)
        return " ".join(r[1] for r in (result or [])).strip()


class TesseractReader(Reader):
    """Tesseract through its command-line program (brew install tesseract / apt install tesseract-ocr)."""
    name = "tesseract"
    follows_instructions = False

    def __init__(self, scale=3, psm=6, lang="eng", binary=None):
        self.binary = binary or shutil.which("tesseract")
        if not self.binary:
            raise ReaderError("tesseract is not on PATH (brew install tesseract)")
        self.scale, self.psm, self.lang = scale, psm, lang

    def read(self, images, prompt=None):
        if len(images) != 1:
            raise ReaderError("tesseract reads one image at a time")
        with Image.open(images[0]) as im, tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "crop.png"
            upscale(im.convert("RGB"), self.scale).save(src)
            run = subprocess.run([self.binary, str(src), "stdout", "--psm", str(self.psm), "-l", self.lang],
                                 capture_output=True, text=True, timeout=60)
        if run.returncode != 0:
            raise ReaderError(f"tesseract failed: {run.stderr.strip()[:200]}")
        return " ".join(run.stdout.split())
