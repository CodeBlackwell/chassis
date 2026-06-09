"""Anthropic adapter for the LLM contract. The SDK import is lazy so this module
loads without `anthropic` installed; the message-split and response-shape helpers
are pure and unit-tested offline."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from lib.contracts import LLMResponse, Message


def _split_system(messages: Sequence[Message]) -> tuple[str, list[dict[str, str]]]:
    system = "\n\n".join(m.content for m in messages if m.role == "system")
    convo = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
    return system, convo


def _shape_anthropic(resp: Any, model: str) -> LLMResponse:
    text = "".join(
        b.text for b in resp.content if getattr(b, "type", "text") == "text"
    )
    usage: dict[str, int] = {}
    if getattr(resp, "usage", None) is not None:
        usage = {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
        }
    return LLMResponse(text=text, model=getattr(resp, "model", model), usage=usage)


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
        temperature: float = 0.0,
        max_tokens: int = 1024,
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
        return _shape_anthropic(self._get_client().messages.create(**kwargs), self.model)


if TYPE_CHECKING:
    from lib.contracts import LLM

    _conforms: type[LLM] = AnthropicLLM
