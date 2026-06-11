"""PassthroughGuardrail: the unopinionated default. It satisfies the Guardrail
contract and is wired through the orchestrator, but enforces nothing — every input
and output passes. What counts as injection, PII, or an ungrounded answer is
domain-specific, so the base ships the seam, not a policy.

A project implements its own Guardrail (whatever input / PII / grounding / judge
logic it needs), registers it under `guardrail` in lib/registry.py, and selects it
in a profile. The orchestrator already honors a blocking verdict, so a real rail
drops in with no other change.
"""

from typing import TYPE_CHECKING

from lib.contracts import Verdict


class PassthroughGuardrail:
    def check_input(self, text: str) -> Verdict:
        return Verdict(passed=True, stage="input")

    def check_output(self, answer: str, contexts: list[str]) -> Verdict:
        return Verdict(passed=True, stage="output")


if TYPE_CHECKING:
    from lib.contracts import Guardrail

    _conforms: type[Guardrail] = PassthroughGuardrail
