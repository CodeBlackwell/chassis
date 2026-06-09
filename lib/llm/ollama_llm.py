"""Ollama adapter for the LLM contract. Uses the local /api/chat endpoint over
stdlib urllib, so it needs no extra dependency — the no-key offline fallback."""

import json
import os
import urllib.request
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from lib.contracts import LLMResponse, Message


def _payload(
    model: str, messages: Sequence[Message], temperature: float, max_tokens: int
) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }


class OllamaLLM:
    def __init__(self, model: str, host: str | None = None) -> None:
        self.model = model
        if host is None:
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.host = host.rstrip("/")

    def chat(
        self,
        messages: Sequence[Message],
        *,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        body = json.dumps(_payload(self.model, messages, temperature, max_tokens)).encode()
        req = urllib.request.Request(
            f"{self.host}/api/chat", data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        return LLMResponse(text=data["message"]["content"], model=self.model)


if TYPE_CHECKING:
    from lib.contracts import LLM

    _conforms: type[LLM] = OllamaLLM
