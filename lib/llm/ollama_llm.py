"""Ollama adapter for the LLM contract. Uses the local /api/chat endpoint over
stdlib urllib, so it needs no extra dependency — the no-key offline fallback."""

import json
import os
import urllib.request
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from config import defaults

from lib.contracts import LLMResponse, Message, ToolCall, ToolSpec

_EMPTY_SCHEMA = {"type": "object", "properties": {}}


def _to_ollama(m: Message) -> dict[str, Any]:
    row: dict[str, Any] = {"role": m.role, "content": m.content}
    if m.tool_calls:
        row["tool_calls"] = [
            {"function": {"name": c.name, "arguments": c.arguments}} for c in m.tool_calls
        ]
    return row


def _payload(
    model: str,
    messages: Sequence[Message],
    temperature: float,
    max_tokens: int,
    tools: Sequence[ToolSpec] = (),
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "messages": [_to_ollama(m) for m in messages],
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    if tools:
        body["tools"] = [
            {"type": "function",
             "function": {"name": t.name, "description": t.description,
                          "parameters": t.parameters or _EMPTY_SCHEMA}}
            for t in tools
        ]
    return body


def _shape_ollama(data: dict[str, Any], model: str) -> LLMResponse:
    msg = data["message"]
    # Ollama returns no call ids; synthesize stable ones for the result round-trip.
    calls = [
        ToolCall(id=f"call_{i}", name=c["function"]["name"],
                 arguments=dict(c["function"].get("arguments") or {}))
        for i, c in enumerate(msg.get("tool_calls") or [])
    ]
    return LLMResponse(text=msg.get("content") or "", model=model, tool_calls=calls)


class OllamaLLM:
    def __init__(self, model: str, host: str | None = None) -> None:
        self.model = model
        if host is None:
            host = os.getenv("OLLAMA_HOST", defaults.OLLAMA_HOST)
        self.host = host.rstrip("/")

    def chat(
        self,
        messages: Sequence[Message],
        *,
        temperature: float = defaults.LLM_TEMPERATURE,
        max_tokens: int = defaults.LLM_MAX_TOKENS,
        tools: Sequence[ToolSpec] = (),
    ) -> LLMResponse:
        body = json.dumps(
            _payload(self.model, messages, temperature, max_tokens, tools)
        ).encode()
        req = urllib.request.Request(
            f"{self.host}/api/chat", data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        return _shape_ollama(data, self.model)


if TYPE_CHECKING:
    from lib.contracts import LLM

    _conforms: type[LLM] = OllamaLLM
