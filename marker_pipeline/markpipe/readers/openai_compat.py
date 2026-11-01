"""Any model behind an OpenAI-compatible chat API: Ollama, vLLM, LM Studio, llama.cpp server, OpenRouter.

    base_url  e.g. http://localhost:11434/v1 (Ollama), http://localhost:8000/v1 (vLLM)
    api_key   read from the environment variable named by `api_key_env`; most local servers need none
Images are sent inline as base64 data URLs. Retries on rate limits and server errors.
"""
import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from .base import Reader, ReaderError, clean_answer

DEFAULT_BASE_URL = "http://localhost:11434/v1"


class OpenAICompatReader(Reader):
    def __init__(self, model, base_url=None, api_key_env="OPENAI_API_KEY", task_prompt=None, max_tokens=64,
                 max_images=2, timeout=120, retries=4, extra_body=None):
        self.name = model
        self.model = model
        self.url = (base_url or os.environ.get("MARKPIPE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/") + "/chat/completions"
        self.api_key = os.environ.get(api_key_env, "") if api_key_env else ""
        self.task_prompt, self.max_tokens, self.timeout, self.retries = task_prompt, max_tokens, timeout, retries
        self.follows_instructions = task_prompt is None
        self.max_images = 1 if task_prompt else max_images
        self.extra_body = extra_body or {}

    @staticmethod
    def _data_url(path):
        mime = mimetypes.guess_type(str(path))[0] or "image/png"
        return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"

    def build_request(self, images, prompt):
        content = [{"type": "image_url", "image_url": {"url": self._data_url(p)}} for p in images]
        content.append({"type": "text", "text": self.task_prompt or prompt})
        return {"model": self.model, "messages": [{"role": "user", "content": content}],
                "max_tokens": self.max_tokens, "temperature": 0, **self.extra_body}

    def read(self, images, prompt):
        if len(images) > self.max_images:
            raise ReaderError(f"{self.name} takes at most {self.max_images} image(s), got {len(images)}")
        body = json.dumps(self.build_request(images, prompt)).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.load(resp)
                return clean_answer(data["choices"][0]["message"].get("content") or "")
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < self.retries:
                    time.sleep(2 ** attempt)
                    continue
                detail = e.read().decode(errors="replace")[:300]
                raise ReaderError(f"{self.name}: HTTP {e.code} from {self.url}: {detail}") from e
            except urllib.error.URLError as e:
                if attempt < self.retries:
                    time.sleep(2 ** attempt)
                    continue
                raise ReaderError(f"{self.name}: cannot reach {self.url} ({e.reason})") from e
            except (KeyError, IndexError, ValueError) as e:
                raise ReaderError(f"{self.name}: unexpected response from {self.url}") from e
