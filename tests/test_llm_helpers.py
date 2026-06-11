from types import SimpleNamespace

from lib.contracts import Message, ToolCall, ToolSpec
from lib.llm.anthropic_llm import _shape_anthropic, _split_system, _tools_anthropic
from lib.llm.ollama_llm import _payload, _shape_ollama
from lib.llm.openai_llm import _shape_openai, _to_openai, _tools_openai


def _msgs():
    return [
        Message("system", "S1"),
        Message("user", "U1"),
        Message("assistant", "A1"),
        Message("system", "S2"),
    ]


def test_split_system_joins_and_filters():
    system, convo = _split_system(_msgs())
    assert system == "S1\n\nS2"
    assert convo == [
        {"role": "user", "content": "U1"},
        {"role": "assistant", "content": "A1"},
    ]


def test_shape_anthropic_concats_text_and_maps_usage():
    resp = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="hel"),
            SimpleNamespace(type="text", text="lo"),
        ],
        usage=SimpleNamespace(input_tokens=3, output_tokens=5),
        model="claude-x",
    )
    out = _shape_anthropic(resp, "fallback")
    assert out.text == "hello"
    assert out.model == "claude-x"
    assert out.usage == {"input_tokens": 3, "output_tokens": 5}


def test_to_openai_maps_all_roles_including_system():
    rows = _to_openai(_msgs())
    assert rows[0] == {"role": "system", "content": "S1"}
    assert len(rows) == 4


def test_shape_openai_pulls_content_and_maps_usage():
    resp = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))],
        usage=SimpleNamespace(prompt_tokens=7, completion_tokens=2),
        model="gpt-x",
    )
    out = _shape_openai(resp, "fallback")
    assert out.text == "answer"
    assert out.model == "gpt-x"
    assert out.usage == {"input_tokens": 7, "output_tokens": 2}


# ---------- tool calling ----------

CALL = ToolCall(id="c1", name="search", arguments={"q": "x"})
SPEC = ToolSpec(name="search", description="look things up")


def _tool_msgs():
    return [
        Message("assistant", "let me check", tool_calls=[CALL]),
        Message("tool", "3 results", tool_call_id="c1"),
    ]


def test_anthropic_maps_tool_turns_to_blocks():
    _, convo = _split_system(_tool_msgs())
    assert convo[0]["content"] == [
        {"type": "text", "text": "let me check"},
        {"type": "tool_use", "id": "c1", "name": "search", "input": {"q": "x"}},
    ]
    assert convo[1] == {
        "role": "user",
        "content": [{"type": "tool_result", "tool_use_id": "c1", "content": "3 results"}],
    }


def test_anthropic_tool_spec_gets_default_schema():
    (shaped,) = _tools_anthropic([SPEC])
    assert shaped["input_schema"] == {"type": "object", "properties": {}}


def test_shape_anthropic_parses_tool_use_blocks():
    resp = SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", id="c1", name="search", input={"q": "x"})],
        usage=None,
        model="claude-x",
    )
    out = _shape_anthropic(resp, "fallback")
    assert out.tool_calls == [CALL]


def test_openai_maps_tool_turns_and_specs():
    rows = _to_openai(_tool_msgs())
    assert rows[0]["tool_calls"][0]["function"] == {
        "name": "search", "arguments": '{"q": "x"}',
    }
    assert rows[1] == {"role": "tool", "content": "3 results", "tool_call_id": "c1"}
    (shaped,) = _tools_openai([SPEC])
    assert shaped["function"]["parameters"] == {"type": "object", "properties": {}}


def test_shape_openai_parses_tool_calls():
    msg = SimpleNamespace(
        content=None,
        tool_calls=[SimpleNamespace(
            id="c1", function=SimpleNamespace(name="search", arguments='{"q": "x"}')
        )],
    )
    resp = SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=None, model="gpt-x")
    out = _shape_openai(resp, "fallback")
    assert out.text == ""
    assert out.tool_calls == [CALL]


def test_ollama_payload_and_shape_round_trip_tools():
    body = _payload("m", _tool_msgs(), 0.0, 10, tools=[SPEC])
    assert body["tools"][0]["function"]["name"] == "search"
    assert body["messages"][0]["tool_calls"] == [
        {"function": {"name": "search", "arguments": {"q": "x"}}}
    ]
    data = {"message": {"content": "", "tool_calls": [
        {"function": {"name": "search", "arguments": {"q": "x"}}}
    ]}}
    out = _shape_ollama(data, "m")
    assert out.tool_calls == [ToolCall(id="call_0", name="search", arguments={"q": "x"})]
