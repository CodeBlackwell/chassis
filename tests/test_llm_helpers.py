from types import SimpleNamespace

from lib.contracts import Message
from lib.llm.anthropic_llm import _shape_anthropic, _split_system
from lib.llm.openai_llm import _shape_openai, _to_openai


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
