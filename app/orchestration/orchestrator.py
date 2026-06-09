"""DefaultOrchestrator: the loop that ties the layers together and is the one seam
the UI and eval consume. handle(query) -> Answer, emitting a TraceEvent at every
decision point. Consumes the Retriever, Memory, and Guardrail contracts; the LLM is
optional (extractive fallback keeps the whole thing runnable offline).

  input rail -> route -> memory context -> specialist -> output rail -> Answer
"""

import time
from typing import TYPE_CHECKING

from lib.contracts import Answer, Turn

from app.orchestration import router, specialists

if TYPE_CHECKING:
    from lib.contracts import LLM, Guardrail, Memory, Retriever
    from lib.trace import TraceBus


class DefaultOrchestrator:
    def __init__(
        self,
        retriever: "Retriever",
        memory: "Memory",
        guardrail: "Guardrail",
        *,
        llm: "LLM | None" = None,
        trace: "TraceBus | None" = None,
        k: int = 5,
    ) -> None:
        self._retriever = retriever
        self._memory = memory
        self._guardrail = guardrail
        self._llm = llm
        self._trace = trace
        self._k = k

    def _emit(self, component: str, event: str, **payload: object) -> None:
        if self._trace:
            self._trace.emit(component, event, **payload)

    def handle(self, query: str) -> Answer:
        verdict_in = self._guardrail.check_input(query)
        self._emit("guardrail.input", "guardrail_verdict", passed=verdict_in.passed,
                   reasons=verdict_in.reasons)
        if not verdict_in.passed:
            self._emit("orchestrator", "answer", route="blocked")
            return Answer(text="Request blocked by the input guardrail.", route="blocked")

        chosen = router.route(query)
        self._emit("router", "route_decision", route=chosen)
        ctx = self._memory.context(query)
        self._emit("memory", "memory_recall", recent=len(ctx.recent), recalled=len(ctx.recalled))

        if chosen == "chitchat":
            answer = specialists.answer_chitchat(query, self._llm)
        elif chosen == "synthesis":
            answer = specialists.answer_synthesis(
                query, self._retriever, self._llm, self._trace, self._k
            )
        else:
            answer = specialists.answer_retrieval(
                query, self._retriever, self._llm, self._trace, self._k
            )

        verdict_out = self._guardrail.check_output(answer.text, answer.contexts)
        self._emit("guardrail.output", "guardrail_verdict", passed=verdict_out.passed,
                   reasons=verdict_out.reasons)
        if not verdict_out.passed:
            answer = Answer(
                text="Response withheld by the output guardrail.",
                route=answer.route,
                citations=answer.citations,
                contexts=answer.contexts,
            )

        now = time.time()
        self._memory.add(Turn(role="user", content=query, ts=now))
        self._memory.add(Turn(role="assistant", content=answer.text, ts=now))
        self._emit("orchestrator", "answer", route=answer.route, citations=len(answer.citations))
        return answer


if TYPE_CHECKING:
    from lib.contracts import Orchestrator

    _conforms: type[Orchestrator] = DefaultOrchestrator
