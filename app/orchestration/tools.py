"""The generic tool-call loop against the LLM contract: call -> execute -> feed
results back, until the model answers in plain text or the round budget runs out.

CHASSIS ships the loop and the seam, not the tools — a project defines ToolSpecs
and a matching handler per tool name. An unknown tool name (model hallucination)
is fed back to the model as an error result rather than raised, so the model can
self-correct; the miss is still traced.
"""

from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any

from config import defaults
from lib.contracts import LLMResponse, Message, ToolSpec

if TYPE_CHECKING:
    from lib.contracts import LLM
    from lib.trace import TraceBus

Handler = Callable[[dict[str, Any]], str]


def run_tool_loop(
    llm: "LLM",
    messages: Sequence[Message],
    tools: Sequence[ToolSpec],
    handlers: Mapping[str, Handler],
    *,
    trace: "TraceBus | None" = None,
    max_iters: int = defaults.TOOL_LOOP_MAX_ITERS,
) -> LLMResponse:
    """max_iters bounds tool rounds, not LLM calls. If the budget runs out the
    last response is returned as-is — callers can check resp.tool_calls."""
    convo = list(messages)
    resp = llm.chat(convo, tools=tools)
    for _ in range(max_iters):
        if not resp.tool_calls:
            break
        convo.append(Message("assistant", resp.text, tool_calls=resp.tool_calls))
        for call in resp.tool_calls:
            handler = handlers.get(call.name)
            result = (
                handler(call.arguments)
                if handler
                else f"error: unknown tool {call.name!r}"
            )
            if trace:
                trace.emit(
                    "tools", "tool_call",
                    name=call.name, known=handler is not None, args=call.arguments,
                )
            convo.append(Message("tool", result, tool_call_id=call.id))
        resp = llm.chat(convo, tools=tools)
    return resp
