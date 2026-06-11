"""OpenAI adapter for the LLM contract. Lazy SDK import; pure helpers tested offline."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from config import defaults

from lib.contracts import LLMResponse, Message


def _to_openai(messages: Sequence[Message]) -> list[dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in messages]


def _shape_openai(resp: Any, model: str) -> LLMResponse:
    text = resp.choices[0].message.content or ""
    usage: dict[str, int] = {}
    if getattr(resp, "usage", None) is not None:
        usage = {
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
        }
    return LLMResponse(text=text, model=getattr(resp, "model", model), usage=usage)


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
    ) -> LLMResponse:
        resp = self._get_client().chat.completions.create(
            model=self.model,
            messages=_to_openai(messages),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return _shape_openai(resp, self.model)


if TYPE_CHECKING:
    from lib.contracts import LLM

    _conforms: type[LLM] = OpenAILLM
