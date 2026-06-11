import pytest
from app.ui import format as fmt
from app.ui.theme import build_css, load_tokens
from lib.contracts import Answer, EvalRow, TraceEvent


def test_tokens_have_light_and_dark():
    tokens = load_tokens()
    assert "light" in tokens and "dark" in tokens
    assert tokens["light"]["accent"]


def test_build_css_emits_vars_and_container():
    css = build_css(load_tokens(), "light")
    assert "--accent:" in css
    assert ".gradio-container" in css


def test_light_and_dark_css_differ():
    tokens = load_tokens()
    assert build_css(tokens, "light") != build_css(tokens, "dark")


def test_source_rows():
    answer = Answer(
        text="x", route="retrieval", citations=["a:0", "b:1"], contexts=["alpha", "beta"]
    )
    rows = fmt.source_rows(answer)
    assert len(rows) == 2
    assert rows[0] == ["a:0", "alpha"]


def test_guardrail_rows_filter_and_shape():
    events = [
        TraceEvent(0.0, "run", "router", "route_decision", {}),
        TraceEvent(
            1.0, "run", "guardrail.input", "guardrail_verdict",
            {"passed": False, "reasons": ["x"]},
        ),
    ]
    rows = fmt.guardrail_rows(events)
    assert len(rows) == 1
    assert rows[0][1] == "guardrail.input"
    assert rows[0][3] == "x"


def test_eval_table_derives_columns_from_scores():
    row = EvalRow("q", "g", answer="a", scores={"judge": 1.0, "faithfulness": 0.5})
    headers, [out] = fmt.eval_table([row])
    assert headers == ["question", "answer", "faithfulness", "judge"]
    assert out == ["q", "a", "0.50", "1.00"]


def test_build_app_constructs():
    pytest.importorskip("gradio")
    from app.ui.app import build_app

    class _Orch:
        def handle(self, query):
            return Answer(text="hi", route="retrieval")

    class _Bus:
        def recent(self, **kwargs):
            return []

    demo = build_app(_Orch(), _Bus())
    assert demo is not None
