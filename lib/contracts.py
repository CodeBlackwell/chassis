"""Frozen contracts for every CHASSIS layer.

These Protocols and dataclasses are the only coupling allowed between layers, and
the only thing a new project has to honor. They are written and frozen before any
layer is built: adapters and app layers code against them and never propose changes
mid-build. If an implementation thinks a contract is wrong, it logs the complaint and
works around it — contract churn is how parallel builds die.

The knowledge-graph option (GraphNode / GraphEdge / GraphStore) was added 2026-06-09
as the single deliberate pre-build extension (extensibility Move 2). Contracts are
re-frozen as of that addition; no further changes in flight.

Rules of engagement:
- Sync everywhere. No async at this scale; it buys nothing and costs debugging time.
- Dataclasses, not Pydantic, for the shared types. Pydantic is allowed inside
  guardrails for schema validation but never leaks into these contracts.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

# ---------- shared types ----------


@dataclass
class Message:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class LLMResponse:
    text: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)


@dataclass
class Chunk:
    id: str
    text: str
    source: str  # file path or doc id
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    chunk: Chunk
    score: float


@dataclass
class GraphNode:
    id: str                  # matches the Chunk.id it was derived from
    kind: str                # domain-defined: "document", "section", "function", ...
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source_id: str           # node id
    target_id: str           # node id
    kind: str                # domain-defined: "contains", "links_to", "calls", ...


@dataclass
class Turn:
    role: Literal["user", "assistant"]
    content: str
    ts: float


@dataclass
class MemoryContext:
    recent: list[Turn]  # short-term window
    recalled: list[SearchResult]  # long-term vector hits
    summary: str | None = None


@dataclass
class Verdict:
    passed: bool
    stage: Literal["input", "output", "judge"]
    reasons: list[str] = field(default_factory=list)


@dataclass
class EvalRow:
    question: str
    ground_truth: str
    answer: str | None = None
    contexts: list[str] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)


@dataclass
class Answer:
    text: str
    route: str = ""  # which specialist (or "chitchat") answered
    citations: list[str] = field(default_factory=list)  # chunk ids backing the answer
    contexts: list[str] = field(default_factory=list)  # raw chunk texts the answer used


@dataclass
class TraceEvent:
    ts: float
    run_id: str
    component: str  # "router", "retriever", "guardrail.input", ...
    event: str  # "route_decision", "search", "block", ...
    payload: dict[str, Any] = field(default_factory=dict)


# ---------- protocols ----------


class LLM(Protocol):
    def chat(
        self,
        messages: Sequence[Message],
        *,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse: ...


class Embedder(Protocol):
    @property
    def dim(self) -> int: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class VectorStore(Protocol):
    def ensure_collection(self, name: str, dim: int) -> None: ...

    def upsert(
        self,
        collection: str,
        chunks: Sequence[Chunk],
        vectors: Sequence[list[float]],
    ) -> None: ...

    def search(
        self,
        collection: str,
        vector: list[float],
        k: int = 5,
    ) -> list[SearchResult]: ...


class GraphStore(Protocol):
    # Optional layer behind a HybridRetriever (vector hit -> graph-expand to
    # connected nodes). Node ids match Chunk ids, so a vector hit maps to a graph
    # seed. Default backend SQLite+NetworkX (in-process); Neo4j is the heavy option.
    def upsert(self, nodes: Sequence[GraphNode], edges: Sequence[GraphEdge]) -> None: ...

    def neighbors(
        self,
        node_id: str,
        *,
        kinds: Sequence[str] | None = None,
        depth: int = 1,
    ) -> list[GraphNode]: ...


class Retriever(Protocol):
    def retrieve(self, query: str, k: int = 5) -> list[SearchResult]: ...


class Orchestrator(Protocol):
    # The one seam the UI and eval both consume. Returns Answer, emits trace.
    def handle(self, query: str) -> Answer: ...


class Memory(Protocol):
    def add(self, turn: Turn) -> None: ...

    def context(self, query: str) -> MemoryContext: ...


class Guardrail(Protocol):
    def check_input(self, text: str) -> Verdict: ...

    def check_output(self, answer: str, contexts: list[str]) -> Verdict: ...


class Evaluator(Protocol):
    def run(self, rows: Sequence[EvalRow]) -> list[EvalRow]: ...
