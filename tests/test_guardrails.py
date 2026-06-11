from app.guardrails.guard import PassthroughGuardrail


def test_passthrough_allows_any_input():
    verdict = PassthroughGuardrail().check_input("any text at all")
    assert verdict.passed
    assert verdict.stage == "input"


def test_passthrough_allows_any_output():
    verdict = PassthroughGuardrail().check_output("any answer", ["any context"])
    assert verdict.passed
    assert verdict.stage == "output"
