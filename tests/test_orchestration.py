from app.guardrails.guard import PassthroughGuardrail
from app.memory.buffer import BufferMemory
from app.orchestration import router
from app.orchestration.orchestrator import DefaultOrchestrator
from lib.contracts import Chunk, Verdict
from lib.embeddings.hashing import HashingEmbedder
from lib.retriever import SimpleRetriever
from lib.trace import TraceBus
from lib.vectorstore.memory_store import MemoryStore


def _seeded_retriever(embedder):
    store = MemoryStore()
    chunks = [
        Chunk(id="d1", text="the trace bus is a deque behind a lock plus a jsonl sink", source="a"),
        Chunk(id="d2", text="profiles select the whole stack by config", source="b"),
    ]
    store.ensure_collection("chassis", embedder.dim)
    store.upsert("chassis", chunks, embedder.embed([c.text for c in chunks]))
    return SimpleRetriever(embedder, store)


def _orch(trace=None, llm=None, memory=None, guardrail=None):
    embedder = HashingEmbedder(dim=512)
    return DefaultOrchestrator(
        _seeded_retriever(embedder),
        memory or BufferMemory(embedder, MemoryStore(), collection="memory"),
        guardrail or PassthroughGuardrail(),
        llm=llm,
        trace=trace,
    )


class _BlockInput:
    def check_input(self, text):
        return Verdict(passed=False, stage="input", reasons=["blocked"])

    def check_output(self, answer, contexts):
        return Verdict(passed=True, stage="output")


_ROUTER_CASES = {
    "what is the trace bus": "retrieval",
    "how does ingestion work": "retrieval",
    "where is the config": "retrieval",
    "list the vector stores": "retrieval",
    "compare qdrant and faiss": "synthesis",
    "summarize the architecture": "synthesis",
    "give an overview of the layers": "synthesis",
    "explain the registry": "synthesis",
    "hello there": "chitchat",
    "thanks for the help": "chitchat",
}


def test_router_accuracy_at_least_9_of_10():
    correct = sum(router.route(q) == expected for q, expected in _ROUTER_CASES.items())
    assert correct >= 9


def test_retrieval_returns_grounded_answer_with_citations():
    answer = _orch().handle("what is the trace bus")
    assert answer.route == "retrieval"
    assert answer.citations
    assert answer.contexts
    assert answer.text in answer.contexts  # extractive => grounded


def test_orchestrator_honors_a_blocking_guardrail():
    answer = _orch(guardrail=_BlockInput()).handle("what is the trace bus")
    assert answer.route == "blocked"
    assert not answer.citations


def test_passthrough_guardrail_does_not_block():
    answer = _orch().handle("what is the trace bus")
    assert answer.route == "retrieval"


def test_chitchat_route_has_no_citations():
    answer = _orch().handle("hello there")
    assert answer.route == "chitchat"
    assert answer.citations == []


def test_emits_at_least_three_trace_events(tmp_path):
    bus = TraceBus("orch", runs_dir=str(tmp_path))
    _orch(trace=bus).handle("what is the trace bus")
    events = [e.event for e in bus.recent()]
    assert "route_decision" in events
    assert "answer" in events
    assert len(events) >= 3


def test_memory_records_user_and_assistant_turns():
    embedder = HashingEmbedder(dim=512)
    memory = BufferMemory(embedder, MemoryStore(), collection="memory")
    _orch(memory=memory).handle("what is the trace bus")
    recent = memory.context("").recent
    assert len(recent) == 2
    assert recent[0].role == "user"
    assert recent[1].role == "assistant"
