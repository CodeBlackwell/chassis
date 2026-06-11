"""OpenAI adapter for the LLM contract. Lazy SDK import; pure helpers tested offline."""

import json
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from config import defaults

from lib.contracts import LLMResponse, Message, ToolCall, ToolSpec

_EMPTY_SCHEMA = {"type": "object", "properties": {}}


def _to_openai(messages: Sequence[Message]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for m in messages:
        row: dict[str, Any] = {"role": m.role, "content": m.content}
        if m.role == "tool":
            row["tool_call_id"] = m.tool_call_id
        if m.tool_calls:
            row["tool_calls"] = [
                {"id": c.id, "type": "function",
                 "function": {"name": c.name, "arguments": json.dumps(c.arguments)}}
                for c in m.tool_calls
            ]
        rows.append(row)
    return rows


def _tools_openai(tools: Sequence[ToolSpec]) -> list[dict[str, Any]]:
    return [
        {"type": "function",
         "function": {"name": t.name, "description": t.description,
                      "parameters": t.parameters or _EMPTY_SCHEMA}}
        for t in tools
    ]


def _shape_openai(resp: Any, model: str) -> LLMResponse:
    msg = resp.choices[0].message
    calls = [
        ToolCall(id=c.id, name=c.function.name,
                 arguments=json.loads(c.function.arguments or "{}"))
        for c in (getattr(msg, "tool_calls", None) or [])
    ]
    usage: dict[str, int] = {}
    if getattr(resp, "usage", None) is not None:
        usage = {
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
        }
    return LLMResponse(
        text=msg.content or "", model=getattr(resp, "model", model),
        usage=usage, tool_calls=calls,
    )


class OpenAILLM:
    def __init__(self, model: str, api_key: str | None = None) -> None:
        import os

        self.model = model
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import openai

            self._client = openai.OpenAI(api_key=self._api_key)
        return self._client

    def chat(
        self,
        messages: Sequence[Message],
        *,
        temperature: float = defaults.LLM_TEMPERATURE,
        max_tokens: int = defaults.LLM_MAX_TOKENS,
        tools: Sequence[ToolSpec] = (),
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": _to_openai(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = _tools_openai(tools)
        return _shape_openai(self._get_client().chat.completions.create(**kwargs), self.model)


if TYPE_CHECKING:
    from lib.contracts import LLM

    _conforms: type[LLM] = OpenAILLM
