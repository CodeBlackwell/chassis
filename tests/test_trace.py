import json

from lib.trace import TraceBus


def test_emit_returns_event_and_buffers(tmp_path):
    bus = TraceBus("run1", runs_dir=str(tmp_path))
    ev = bus.emit("router", "route_decision", route="retrieval")
    assert ev.component == "router"
    assert ev.payload["route"] == "retrieval"
    assert len(bus.recent()) == 1


def test_jsonl_sink_written(tmp_path):
    bus = TraceBus("run2", runs_dir=str(tmp_path))
    bus.emit("retriever", "retrieval", k=5)
    lines = (tmp_path / "run2.jsonl").read_text().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["component"] == "retriever"
    assert rec["payload"]["k"] == 5


def test_recent_filters_by_prefix(tmp_path):
    bus = TraceBus("run3", runs_dir=str(tmp_path))
    bus.emit("router", "route_decision")
    bus.emit("guardrail.input", "guardrail_verdict")
    bus.emit("guardrail.output", "guardrail_verdict")
    assert len(bus.recent(component_prefix="guardrail")) == 2
    assert len(bus.recent(component_prefix="router")) == 1


def test_ring_buffer_caps_at_500(tmp_path):
    bus = TraceBus("run4", runs_dir=str(tmp_path))
    for i in range(550):
        bus.emit("llm", "llm_call", i=i)
    assert len(bus.recent()) == 500
