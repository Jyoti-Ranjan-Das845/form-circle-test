"""The reader interface: something that turns a crop image into text."""
import re
from abc import ABC, abstractmethod


class ReaderError(RuntimeError):
    """A reader could not be created or could not answer."""


class Reader(ABC):
    name = "reader"
    follows_instructions = True  # False: an OCR model or engine that ignores our prompt

    @abstractmethod
    def read(self, image, prompt):
        """The text in `image` (a path). `prompt` is the instruction, ignored by readers that don't follow one."""

    def close(self):
        """Free the model. Safe to call more than once."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")


def clean_answer(text):
    """Strip what models wrap around an answer: reasoning blocks, chat-template tags, code fences, quotes."""
    text = _THINK.sub("", text or "")
    if "</think>" in text:  # reasoning without an opening tag
        text = text.split("</think>", 1)[1]
    text = re.split(r"<channel\|>", text)[-1]  # Gemma 4 thought channel
    for tag in ("<turn|>", "<|im_end|>", "<|endoftext|>", "</s>", "<end_of_turn>"):
        text = text.replace(tag, "")
    text = _FENCE.sub("", text.strip()).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'`":
        text = text[1:-1].strip()
    return text
