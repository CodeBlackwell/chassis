"""BufferMemory: a short-term window plus long-term vector recall, satisfying the
Memory contract. Every turn is appended to a deque (the window) and embedded into
its own vector collection (long-term). When the window overflows, the evicted turn
folds into a running summary. Evicted turns stay recallable via the vector store,
so a fact from turn 1 is still found at turn 20.

Without an LLM the summary is a plain running transcript, so it works offline.
"""

from collections import deque
from typing import TYPE_CHECKING

from lib.contracts import Chunk, MemoryContext, Message, Turn

if TYPE_CHECKING:
    from lib.contracts import LLM, Embedder, SearchResult, VectorStore


class BufferMemory:
    def __init__(
        self,
        embedder: "Embedder",
        store: "VectorStore",
        *,
        window: int = 8,
        recall_k: int = 3,
        collection: str = "memory",
        llm: "LLM | None" = None,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._window = window
        self._recall_k = recall_k
        self._collection = collection
        self._llm = llm
        self._recent: deque[Turn] = deque()
        self._summary: str | None = None
        self._counter = 0
        store.ensure_collection(collection, embedder.dim)

    def add(self, turn: Turn) -> None:
        self._recent.append(turn)
        chunk = Chunk(
            id=f"{self._collection}:{self._counter}",
            text=turn.content,
            source="memory",
            meta={"role": turn.role, "ts": turn.ts},
        )
        self._counter += 1
        self._store.upsert(self._collection, [chunk], self._embedder.embed([turn.content]))
        while len(self._recent) > self._window:
            self._summary = self._summarize(self._summary, self._recent.popleft())

    def context(self, query: str) -> MemoryContext:
        recalled: list[SearchResult] = []
        if query.strip():
            vector = self._embedder.embed([query])[0]
            recalled = self._store.search(self._collection, vector, k=self._recall_k)
        return MemoryContext(recent=list(self._recent), recalled=recalled, summary=self._summary)

    def _summarize(self, prior: str | None, turn: Turn) -> str:
        snippet = f"{turn.role}: {turn.content}"
        if self._llm is None:
            return f"{prior}\n{snippet}" if prior else snippet
        prompt = (
            "Update the running summary with the new turn; return only the summary.\n\n"
            f"Summary:\n{prior or '(empty)'}\n\nNew turn — {snippet}"
        )
        return self._llm.chat([Message("user", prompt)], max_tokens=200).text


if TYPE_CHECKING:
    from lib.contracts import Memory

    _conforms: type[Memory] = BufferMemory
