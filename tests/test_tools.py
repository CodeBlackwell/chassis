from app.orchestration.tools import run_tool_loop
from lib.contracts import LLMResponse, Message, ToolCall, ToolSpec

SEARCH = ToolSpec(name="search", description="look things up")


class FakeLLM:
    """Pops a scripted response per chat() call and records each convo seen."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.seen = []

    def chat(self, messages, *, temperature=0.0, max_tokens=1024, tools=()):
        self.seen.append(list(messages))
        return self.responses.pop(0)


def _resp(text="", calls=()):
    return LLMResponse(text=text, model="fake", tool_calls=list(calls))


def test_no_tool_calls_returns_first_response():
    llm = FakeLLM([_resp(text="direct answer")])
    out = run_tool_loop(llm, [Message("user", "q")], [SEARCH], {})
    assert out.text == "direct answer"
    assert len(llm.seen) == 1


def test_executes_handler_and_feeds_result_back():
    call = ToolCall(id="c1", name="search", arguments={"q": "rent policy"})
    llm = FakeLLM([_resp(calls=[call]), _resp(text="found it")])
    seen_args = []
    out = run_tool_loop(
        llm, [Message("user", "q")], [SEARCH],
        {"search": lambda args: seen_args.append(args) or "3 results"},
    )
    assert out.text == "found it"
    assert seen_args == [{"q": "rent policy"}]
    final_convo = llm.seen[1]
    assert final_convo[1].tool_calls == [call]  # assistant turn replayed with its calls
    assert final_convo[2].role == "tool"
    assert final_convo[2].content == "3 results"
    assert final_convo[2].tool_call_id == "c1"


def test_unknown_tool_feeds_error_back_instead_of_raising():
    call = ToolCall(id="c1", name="made_up", arguments={})
    llm = FakeLLM([_resp(calls=[call]), _resp(text="ok")])
    out = run_tool_loop(llm, [Message("user", "q")], [SEARCH], {})
    assert out.text == "ok"
    assert "unknown tool" in llm.seen[1][2].content


def test_round_budget_returns_last_response_with_calls_pending():
    call = ToolCall(id="c1", name="search", arguments={})
    llm = FakeLLM([_resp(calls=[call])] * 3)
    out = run_tool_loop(
        llm, [Message("user", "q")], [SEARCH], {"search": lambda a: "r"}, max_iters=2
    )
    assert out.tool_calls  # budget exhausted, calls left unanswered
    assert len(llm.seen) == 3  # initial call + 2 rounds
