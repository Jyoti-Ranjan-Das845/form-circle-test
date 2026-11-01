"""Choose a reader by a short spec string.

    paddleocr-vl, qwen3.5-4b, ...   a preset (see PRESETS / `python -m markpipe readers`)
    mlx:<huggingface repo>          any mlx-vlm model, e.g. mlx:mlx-community/Qwen3-VL-2B-Instruct-bf16
    openai:<model name>             any OpenAI-compatible server, e.g. openai:qwen2.5vl:7b with Ollama
    rapidocr, tesseract             classic OCR engines
Keyword options (task_prompt, thinking, base_url, max_tokens, ...) are passed to the reader's constructor.
"""
import inspect

from .base import Reader, ReaderError, clean_answer

# name: (backend, constructor arguments, description)
PRESETS = {
    "paddleocr-vl": ("mlx", dict(repo="mlx-community/PaddleOCR-VL-1.5-bf16", task_prompt="OCR:"),
                     "PaddleOCR-VL 1.5, 0.9B, bf16 (unquantized). OCR model: fixed 'OCR:' prompt"),
    "paddleocr-vl-1.6-4bit": ("mlx", dict(repo="mlx-community/PaddleOCR-VL-1.6-4bit", task_prompt="OCR:"),
                              "PaddleOCR-VL 1.6, 4-bit (no bf16 build of 1.6 on mlx-community)"),
    "qwen3.5-4b": ("mlx", dict(repo="mlx-community/Qwen3.5-4B-6bit", thinking=False),
                   "Qwen3.5-4B, 6-bit, thinking off. Follows instructions"),
    "qwen3.5-9b": ("mlx", dict(repo="mlx-community/Qwen3.5-9B-4bit", thinking=False),
                   "Qwen3.5-9B, 4-bit, thinking off (needs ~6 GB of GPU memory)"),
    "qwen3-vl-2b": ("mlx", dict(repo="mlx-community/Qwen3-VL-2B-Instruct-bf16"), "Qwen3-VL-2B Instruct, bf16"),
    "gemma4-e2b": ("mlx", dict(repo="mlx-community/gemma-4-e2b-it-6bit"), "Gemma 4 E2B, 6-bit"),
    "glm-ocr": ("mlx", dict(repo="mlx-community/GLM-OCR-bf16", task_prompt="Text Recognition:"),
                "GLM-OCR, bf16. OCR model: fixed prompt"),
    "rapidocr": ("rapidocr", {}, "PP-OCR via ONNX Runtime (CPU)"),
    "tesseract": ("tesseract", {}, "Tesseract command-line OCR (CPU)"),
}


def _reader_class(backend):
    # imported lazily so a missing optional dependency only matters for the backend that needs it
    if backend == "mlx":
        from .mlx_vlm import MLXVLMReader
        return MLXVLMReader
    if backend == "openai":
        from .openai_compat import OpenAICompatReader
        return OpenAICompatReader
    if backend == "rapidocr":
        from .ocr_engines import RapidOCRReader
        return RapidOCRReader
    if backend == "tesseract":
        from .ocr_engines import TesseractReader
        return TesseractReader
    raise ReaderError(f"unknown backend {backend!r}")


def parse_spec(spec):
    """(backend, constructor arguments) for a spec string, without loading anything."""
    spec = spec.strip()
    if spec in PRESETS:
        backend, kwargs, _ = PRESETS[spec]
        return backend, {**kwargs, **({"name": spec} if backend == "mlx" else {})}
    prefix, sep, rest = spec.partition(":")
    if sep and prefix == "mlx" and rest:
        return "mlx", {"repo": rest}
    if sep and prefix == "openai" and rest:
        return "openai", {"model": rest}
    raise ReaderError(f"unknown reader {spec!r}; use a preset ({', '.join(PRESETS)}), mlx:<repo> or openai:<model>")


def create_reader(spec, **options):
    """A ready reader. Options set to None are ignored, so CLI defaults don't override presets."""
    backend, kwargs = parse_spec(spec)
    cls = _reader_class(backend)
    accepted = set(inspect.signature(cls.__init__).parameters) - {"self"}
    given = {k: v for k, v in options.items() if v is not None}
    unknown = sorted(set(given) - accepted)
    if unknown:
        raise ReaderError(f"option(s) {', '.join(unknown)} do not apply to {spec!r} (accepts: {', '.join(sorted(accepted))})")
    return cls(**{**kwargs, **given})


__all__ = ["PRESETS", "Reader", "ReaderError", "clean_answer", "create_reader", "parse_spec"]
