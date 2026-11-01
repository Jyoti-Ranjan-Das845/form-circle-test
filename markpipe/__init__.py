"""markpipe: read pen-circled text on scanned pages.

    detect   compare the marked page with its clean original; box and classify every pen mark
    crop     cut out what each circle encloses (from the clean page, nothing else in the crop)
    read     send the crops to a pluggable reader: an MLX vision model (PaddleOCR-VL, Qwen, ...),
             any OpenAI-compatible server, or a classic OCR engine
"""
from .config import DetectorConfig
from .dataset import PagePair, find_pairs
from .detect import Marker, PageMismatchError, detect
from .pipeline import detect_pages, read_crops
from .readers import PRESETS, Reader, ReaderError, create_reader

__version__ = "0.1.0"
__all__ = ["DetectorConfig", "Marker", "PRESETS", "PagePair", "PageMismatchError", "Reader", "ReaderError",
           "create_reader", "detect", "detect_pages", "find_pairs", "read_crops"]
