import pytest
from lib.contracts import Answer, TraceEvent


class _Orch:
    def handle(self, query):
        return Answer(
            text=f"echo:{query}", route="retrieval", citations=["a:0"], contexts=["alpha"]
        )


class _Bus:
    def recent(self, component_prefix=""):
        events = [
            TraceEvent(0.0, "run", "router", "route_decision", {}),
            TraceEvent(1.0, "run", "guardrail.input", "guardrail_verdict", {"passed": True}),
        ]
        return [e for e in events if e.component.startswith(component_prefix)]


@pytest.fixture()
def client():
    pytest.importorskip("fastapi")
    from app.api.app import create_app
    from fastapi.testclient import TestClient

    return TestClient(create_app(_Orch(), _Bus()))


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_round_trips_the_answer_dataclass(client):
    body = client.post("/ask", json={"query": "hi"}).json()
    assert body == {
        "text": "echo:hi", "route": "retrieval", "citations": ["a:0"], "contexts": ["alpha"],
    }


def test_ask_without_query_is_422(client):
    assert client.post("/ask", json={}).status_code == 422


def test_trace_filters_by_component_prefix(client):
    assert len(client.get("/trace").json()) == 2
    events = client.get("/trace", params={"component": "guardrail"}).json()
    assert len(events) == 1
    assert events[0]["payload"] == {"passed": True}


def test_no_bus_means_empty_trace():
    pytest.importorskip("fastapi")
    from app.api.app import create_app
    from fastapi.testclient import TestClient

    assert TestClient(create_app(_Orch())).get("/trace").json() == []
