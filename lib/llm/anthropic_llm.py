"""Anthropic adapter for the LLM contract. The SDK import is lazy so this module
loads without `anthropic` installed; the message-split, tool-shaping, and
response-shape helpers are pure and unit-tested offline."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from config import defaults

from lib.contracts import LLMResponse, Message, ToolCall, ToolSpec

_EMPTY_SCHEMA = {"type": "object", "properties": {}}


def _to_anthropic(m: Message) -> dict[str, Any]:
    if m.role == "tool":
        # Anthropic carries tool results as tool_result blocks in a user message.
        return {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": m.tool_call_id, "content": m.content}
            ],
        }
    if m.tool_calls:
        blocks: list[dict[str, Any]] = []
        if m.content:
            blocks.append({"type": "text", "text": m.content})
        blocks += [
            {"type": "tool_use", "id": c.id, "name": c.name, "input": c.arguments}
            for c in m.tool_calls
        ]
        return {"role": m.role, "content": blocks}
    return {"role": m.role, "content": m.content}


def _split_system(messages: Sequence[Message]) -> tuple[str, list[dict[str, Any]]]:
    system = "\n\n".join(m.content for m in messages if m.role == "system")
    convo = [_to_anthropic(m) for m in messages if m.role != "system"]
    return system, convo


def _tools_anthropic(tools: Sequence[ToolSpec]) -> list[dict[str, Any]]:
    return [
        {"name": t.name, "description": t.description,
         "input_schema": t.parameters or _EMPTY_SCHEMA}
        for t in tools
    ]


def _shape_anthropic(resp: Any, model: str) -> LLMResponse:
    text = "".join(
        b.text for b in resp.content if getattr(b, "type", "text") == "text"
    )
    calls = [
        ToolCall(id=b.id, name=b.name, arguments=dict(b.input))
        for b in resp.content
        if getattr(b, "type", "") == "tool_use"
    ]
    usage: dict[str, int] = {}
    if getattr(resp, "usage", None) is not None:
        usage = {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
        }
    return LLMResponse(
        text=text, model=getattr(resp, "model", model), usage=usage, tool_calls=calls
    )


class AnthropicLLM:
    def __init__(self, model: str, api_key: str | None = None) -> None:
        import os

        self.model = model
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def chat(
        self,
        messages: Sequence[Message],
        *,
        temperature: float = defaults.LLM_TEMPERATURE,
        max_tokens: int = defaults.LLM_MAX_TOKENS,
        tools: Sequence[ToolSpec] = (),
    ) -> LLMResponse:
        system, convo = _split_system(messages)
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": convo,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = _tools_anthropic(tools)
        return _shape_anthropic(self._get_client().messages.create(**kwargs), self.model)


if TYPE_CHECKING:
    from lib.contracts import LLM

    _conforms: type[LLM] = AnthropicLLM
