"""Specialists produce an Answer for a route. With an LLM they synthesize a
grounded answer from the retrieved context; without one they fall back to an
extractive answer (top chunk / joined snippets), so the pipeline runs offline.
"""

from typing import TYPE_CHECKING

from config import defaults
from lib.contracts import Answer, Message

if TYPE_CHECKING:
    from typing import Protocol

    from lib.contracts import LLM, Retriever, SearchResult, Tracer

    class SpecialistFn(Protocol):
        def __call__(
            self,
            query: str,
            *,
            retriever: "Retriever",
            llm: "LLM | None",
            trace: "Tracer | None",
            k: int,
        ) -> Answer: ...

_NO_INFO = "I don't have information on that in the ingested documents."


def _gather(
    query: str, retriever: "Retriever", k: int, trace: "Tracer | None"
) -> tuple[list["SearchResult"], list[str], list[str]]:
    hits = retriever.retrieve(query, k=k)
    if trace:
        trace.emit("retriever", "retrieval", k=k, hits=len(hits))
    return hits, [h.chunk.text for h in hits], [h.chunk.id for h in hits]


def _synthesize(llm: "LLM", query: str, contexts: list[str]) -> str:
    prompt = (
        "Answer the question using only the context below. If the context is "
        "insufficient, say so.\n\nContext:\n"
        + "\n---\n".join(contexts)
        + f"\n\nQuestion: {query}"
    )
    return llm.chat([Message("user", prompt)]).text


def answer_retrieval(
    query: str,
    retriever: "Retriever",
    llm: "LLM | None",
    trace: "Tracer | None",
    k: int = defaults.RETRIEVAL_K,
) -> Answer:
    hits, contexts, citations = _gather(query, retriever, k, trace)
    if not hits:
        return Answer(text=_NO_INFO, route="retrieval")
    text = _synthesize(llm, query, contexts) if llm else hits[0].chunk.text
    return Answer(text=text, route="retrieval", citations=citations, contexts=contexts)


def answer_synthesis(
    query: str,
    retriever: "Retriever",
    llm: "LLM | None",
    trace: "Tracer | None",
    k: int = defaults.RETRIEVAL_K,
) -> Answer:
    hits, contexts, citations = _gather(query, retriever, k, trace)
    if not hits:
        return Answer(text=_NO_INFO, route="synthesis")
    text = (
        _synthesize(llm, query, contexts)
        if llm
        else " … ".join(
            c[: defaults.EXTRACTIVE_SNIPPET_CHARS]
            for c in contexts[: defaults.EXTRACTIVE_MAX_SNIPPETS]
        )
    )
    return Answer(text=text, route="synthesis", citations=citations, contexts=contexts)


def answer_chitchat(query: str, llm: "LLM | None") -> Answer:
    if llm is None:
        return Answer(text="Hi. Ask me about the ingested documents.", route="chitchat")
    return Answer(text=llm.chat([Message("user", query)]).text, route="chitchat")


def _chitchat(
    query: str,
    *,
    retriever: "Retriever",
    llm: "LLM | None",
    trace: "Tracer | None",
    k: int,
) -> Answer:
    return answer_chitchat(query, llm)


def _retrieval(
    query: str,
    *,
    retriever: "Retriever",
    llm: "LLM | None",
    trace: "Tracer | None",
    k: int,
) -> Answer:
    return answer_retrieval(query, retriever, llm, trace, k)


def _synthesis(
    query: str,
    *,
    retriever: "Retriever",
    llm: "LLM | None",
    trace: "Tracer | None",
    k: int,
) -> Answer:
    return answer_synthesis(query, retriever, llm, trace, k)


# Route name -> uniform-signature specialist. The orchestrator dispatches on this
# (or on a map a project injects); add a route by adding an entry, not an elif.
SPECIALISTS: dict[str, "SpecialistFn"] = {
    "retrieval": _retrieval,
    "synthesis": _synthesis,
    "chitchat": _chitchat,
}
