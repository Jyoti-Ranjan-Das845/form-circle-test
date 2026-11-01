"""Any vision-language model that mlx-vlm can load (Apple Silicon), e.g. PaddleOCR-VL, Qwen3.5, Gemma 4.

OCR-specialised models are trained on a fixed task prompt ("OCR:" for PaddleOCR-VL); pass it as `task_prompt` and
our instruction is not sent. Chat models get the instruction. `thinking` switches reasoning on/off for models that
support it (Qwen3.5); None leaves the model's default.
"""
import gc
import logging
import time

from .base import Reader, ReaderError, clean_answer

log = logging.getLogger(__name__)


class MLXVLMReader(Reader):
    def __init__(self, repo, task_prompt=None, thinking=None, max_tokens=64, name=None):
        try:
            from mlx_vlm import generate, load
            from mlx_vlm.prompt_utils import apply_chat_template
        except ImportError as e:
            raise ReaderError("mlx-vlm is not installed (pip install mlx-vlm); it needs Apple Silicon") from e
        self.name = name or repo
        self.repo, self.task_prompt, self.thinking, self.max_tokens = repo, task_prompt, thinking, max_tokens
        self.follows_instructions = task_prompt is None
        self._generate, self._template = generate, apply_chat_template
        t0 = time.time()
        try:
            self._model, self._processor = load(repo)
        except Exception as e:
            raise ReaderError(f"could not load {repo}: {e}") from e
        log.info("loaded %s in %.0fs", repo, time.time() - t0)
        self._chat = {}

    def _chat_prompt(self, prompt):
        if prompt not in self._chat:
            kwargs = {} if self.thinking is None else {"enable_thinking": self.thinking}
            try:
                self._chat[prompt] = self._template(self._processor, self._model.config, prompt, num_images=1, **kwargs)
            except Exception as e:  # some OCR models ship without a chat template
                log.warning("%s: no usable chat template (%s), sending the raw prompt", self.name, e)
                self._chat[prompt] = prompt
        return self._chat[prompt]

    def read(self, image, prompt):
        if self._model is None:
            raise ReaderError(f"{self.name} is closed")
        chat = self._chat_prompt(self.task_prompt or prompt)
        result = self._generate(self._model, self._processor, chat, image=[str(image)],
                                max_tokens=self.max_tokens, temperature=0.0, verbose=False)
        return clean_answer(getattr(result, "text", result))

    def close(self):
        if getattr(self, "_model", None) is not None:
            self._model = self._processor = None
            self._chat.clear()
            gc.collect()
            try:
                import mlx.core as mx
                mx.clear_cache()
            except Exception:  # older mlx versions; memory is freed when the process ends
                pass
