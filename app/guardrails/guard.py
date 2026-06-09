"""DefaultGuardrail: composes the pure checks into the Guardrail contract. Input
rail = length + injection + PII (refuse-by-default: any hit blocks). Output rail =
non-empty + grounded-in-context, plus an optional LLM safety judge when an LLM is
supplied. Deterministic without an LLM, so it tests fully offline.
"""

from typing import TYPE_CHECKING

from lib.contracts import Message, Verdict

from app.guardrails import checks

if TYPE_CHECKING:
    from lib.contracts import LLM


class DefaultGuardrail:
    def __init__(self, llm: "LLM | None" = None, max_input_chars: int = checks.MAX_INPUT_CHARS):
        self._llm = llm
        self._max = max_input_chars

    def check_input(self, text: str) -> Verdict:
        reasons: list[str] = []
        ok, reason = checks.check_length(text, self._max)
        if reason:
            reasons.append(reason)
        reasons += checks.check_injection(text)[1]
        reasons += checks.check_pii(text)[1]
        return Verdict(passed=not reasons, stage="input", reasons=reasons)

    def check_output(self, answer: str, contexts: list[str]) -> Verdict:
        reasons: list[str] = []
        if not answer.strip():
            reasons.append("empty_answer")
        ok, reason = checks.check_grounded(answer, contexts)
        if reason:
            reasons.append(reason)
        if self._llm is not None and (judged := self._judge(answer)):
            reasons.append(judged)
        return Verdict(passed=not reasons, stage="output", reasons=reasons)

    def _judge(self, answer: str) -> str | None:
        assert self._llm is not None
        prompt = (
            "You are a safety classifier. Reply with exactly SAFE or UNSAFE.\n\nAnswer:\n" + answer
        )
        resp = self._llm.chat([Message("user", prompt)], max_tokens=5)
        return "judge:unsafe" if "UNSAFE" in resp.text.upper() else None


if TYPE_CHECKING:
    from lib.contracts import Guardrail

    _conforms: type[Guardrail] = DefaultGuardrail
