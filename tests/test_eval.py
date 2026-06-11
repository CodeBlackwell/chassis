from collections.abc import Sequence

from app.eval import metrics
from app.eval.dataset import generate
from app.eval.evaluator import RagasEvaluator, summary, to_csv
from app.eval.runner import answer_rows, report
from app.guardrails.guard import PassthroughGuardrail
from app.memory.buffer import BufferMemory
from app.orchestration.orchestrator import DefaultOrchestrator
from lib.contracts import Chunk, EvalRow, LLMResponse, Message
from lib.embeddings.hashing import HashingEmbedder
from lib.retriever import SimpleRetriever
from lib.vectorstore.memory_store import MemoryStore


class FakeLLM:
    def __init__(self, text: str) -> None:
        self._text = text

    def chat(self, messages: Sequence[Message], *, temperature=0.0, max_tokens=1024) -> LLMResponse:
        return LLMResponse(text=self._text, model="fake")


def test_metrics_in_range_and_grounded_high():
    score = metrics.faithfulness("the trace bus is a deque", ["the trace bus is a deque and lock"])
    assert 0.0 <= score <= 1.0
    assert score > 0.9
    assert metrics.answer_relevance("", "question") == 0.0
    assert metrics.context_precision([], "truth") == 0.0


def test_faithfulness_catches_fabrication():
    grounded = metrics.faithfulness("trace bus deque", ["the trace bus is a deque behind a lock"])
    fabricated = metrics.faithfulness("bananas grow in orchards", ["the trace bus is a deque"])
    assert grounded > fabricated


def test_evaluator_fills_three_scores():
    row = EvalRow(
        question="what is the trace bus",
        ground_truth="a deque behind a lock",
        answer="the trace bus is a deque behind a lock",
        contexts=["the trace bus is a deque behind a lock"],
    )
    [scored] = RagasEvaluator().run([row])
    for key in ("faithfulness", "answer_relevance", "context_precision"):
        assert 0.0 <= scored.scores[key] <= 1.0
    assert "judge" not in scored.scores


def test_evaluator_adds_judge_with_llm():
    row = EvalRow(question="q", ground_truth="g", answer="a", contexts=["a"])
    [scored] = RagasEvaluator(llm=FakeLLM("0.9")).run([row])
    assert scored.scores["judge"] == 0.9


def test_summary_means():
    rows = [
        EvalRow("q", "g", scores={"faithfulness": 0.5}),
        EvalRow("q", "g", scores={"faithfulness": 1.0}),
    ]
    assert summary(rows)["faithfulness"] == 0.75


def test_to_csv_writes_header_and_scores(tmp_path):
    out = tmp_path / "r.csv"
    to_csv([EvalRow("q", "g", answer="a", scores={"faithfulness": 0.5})], str(out))
    content = out.read_text()
    assert "question" in content
    assert "0.500" in content


def _orchestrator():
    embedder = HashingEmbedder(dim=512)
    store = MemoryStore()
    chunks = [Chunk(id="d1", text="the trace bus is a deque behind a lock", source="a")]
    store.ensure_collection("chassis", embedder.dim)
    store.upsert("chassis", chunks, embedder.embed([c.text for c in chunks]))
    return DefaultOrchestrator(
        SimpleRetriever(embedder, store),
        BufferMemory(embedder, MemoryStore(), collection="memory"),
        PassthroughGuardrail(),
    )


def test_runner_fills_rows_and_reports():
    rows = [EvalRow(question="what is the trace bus", ground_truth="a deque behind a lock")]
    filled = answer_rows(_orchestrator(), rows)
    assert filled[0].answer
    assert filled[0].contexts
    text = report(RagasEvaluator().run(filled))
    assert "faithfulness" in text


def test_dataset_generate_offline(tmp_path):
    (tmp_path / "a.md").write_text("CHASSIS is a contracts-first multi-agent RAG base repo.")
    (tmp_path / "b.txt").write_text("Profiles select the whole stack by config.")
    rows = generate(str(tmp_path), n=10)
    assert len(rows) == 2
    assert all(r.question and r.ground_truth for r in rows)
