"""Any model behind an OpenAI-compatible chat API: Ollama, vLLM, LM Studio, llama.cpp server, OpenRouter.

    base_url  e.g. http://localhost:11434/v1 (Ollama), http://localhost:8000/v1 (vLLM); or set MARKPIPE_BASE_URL
    api_key   read from the environment variable named by `api_key_env`; most local servers need none
The crop is sent inline as a base64 data URL. Retries on rate limits, server errors and connection failures.
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
_RETRY_CODES = {429, 500, 502, 503, 504}


class OpenAICompatReader(Reader):
    def __init__(self, model, base_url=None, api_key_env="OPENAI_API_KEY", task_prompt=None, max_tokens=64,
                 timeout=120, retries=4, extra_body=None):
        self.name = self.model = model
        self.url = (base_url or os.environ.get("MARKPIPE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/") + "/chat/completions"
        self.api_key = os.environ.get(api_key_env, "") if api_key_env else ""
        self.task_prompt, self.max_tokens, self.timeout, self.retries = task_prompt, max_tokens, timeout, retries
        self.follows_instructions = task_prompt is None
        self.extra_body = extra_body or {}

    def build_request(self, image, prompt):
        mime = mimetypes.guess_type(str(image))[0] or "image/png"
        url = f"data:{mime};base64,{base64.b64encode(Path(image).read_bytes()).decode()}"
        content = [{"type": "image_url", "image_url": {"url": url}},
                   {"type": "text", "text": self.task_prompt or prompt}]
        return {"model": self.model, "messages": [{"role": "user", "content": content}],
                "max_tokens": self.max_tokens, "temperature": 0, **self.extra_body}

    def read(self, image, prompt):
        body = json.dumps(self.build_request(image, prompt)).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        for attempt in range(self.retries + 1):
            last = attempt == self.retries
            req = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.load(resp)
                return clean_answer(data["choices"][0]["message"].get("content") or "")
            except urllib.error.HTTPError as e:
                if e.code in _RETRY_CODES and not last:
                    time.sleep(2 ** attempt)
                    continue
                detail = e.read().decode(errors="replace")[:300]
                raise ReaderError(f"{self.name}: HTTP {e.code} from {self.url}: {detail}") from e
            except urllib.error.URLError as e:
                if not last:
                    time.sleep(2 ** attempt)
                    continue
                raise ReaderError(f"{self.name}: cannot reach {self.url} ({e.reason})") from e
            except (KeyError, IndexError, ValueError) as e:
                raise ReaderError(f"{self.name}: unexpected response from {self.url}") from e
