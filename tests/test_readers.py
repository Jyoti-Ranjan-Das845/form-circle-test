"""Reader selection and answer clean-up. No model is loaded."""
import json

import pytest

from markpipe.readers import PRESETS, ReaderError, clean_answer, create_reader, parse_spec
from markpipe.readers.openai_compat import OpenAICompatReader


def test_presets_parse():
    for name in PRESETS:
        backend, kwargs = parse_spec(name)
        assert backend in {"mlx", "rapidocr", "tesseract"}


def test_generic_specs():
    assert parse_spec("mlx:mlx-community/SomeModel") == ("mlx", {"repo": "mlx-community/SomeModel"})
    assert parse_spec("openai:qwen2.5vl:7b") == ("openai", {"model": "qwen2.5vl:7b"})
    with pytest.raises(ReaderError):
        parse_spec("nope")


def test_paddleocr_uses_its_task_prompt():
    backend, kwargs = parse_spec("paddleocr-vl")
    assert backend == "mlx" and kwargs["task_prompt"] == "OCR:" and "bf16" in kwargs["repo"]


def test_options_that_do_not_apply_are_rejected():
    with pytest.raises(ReaderError, match="base_url"):
        create_reader("tesseract", base_url="http://x")


def test_none_options_are_ignored():
    reader = create_reader("openai:m", base_url="http://localhost:1/v1", task_prompt=None)
    assert reader.follows_instructions and reader.url == "http://localhost:1/v1/chat/completions"


def test_openai_request(tmp_path):
    img = tmp_path / "c.png"
    img.write_bytes(b"\x89PNG fake")
    body = OpenAICompatReader("m", base_url="http://h/v1").build_request(img, "what?")
    content = body["messages"][0]["content"]
    assert content[0]["image_url"]["url"].startswith("data:image/png;base64,")
    assert content[-1] == {"type": "text", "text": "what?"}
    json.dumps(body)


def test_openai_unreachable_server(tmp_path):
    img = tmp_path / "c.png"
    img.write_bytes(b"x")
    reader = OpenAICompatReader("m", base_url="http://127.0.0.1:9/v1", retries=0, timeout=2)
    with pytest.raises(ReaderError, match="cannot reach"):
        reader.read(img, "q")


@pytest.mark.parametrize("raw, expected", [
    ("Boston", "Boston"),
    ("<think>hmm</think>\nBoston", "Boston"),
    ("reasoning...</think> Boston", "Boston"),
    ("```\nBoston\n```", "Boston"),
    ('"Boston"', "Boston"),
    ("Boston<|im_end|>", "Boston"),
    ("", ""),
])
def test_clean_answer(raw, expected):
    assert clean_answer(raw) == expected
