"""Corpus-agnostic seed-set generation: sample chunks from the freshly ingested
corpus and turn each into a (question, ground_truth) EvalRow. With an LLM the
system writes its own exam; without one, a degenerate fallback keeps it offline.
"""

from typing import TYPE_CHECKING

from lib.contracts import EvalRow, Message
from lib.ingestion.pipeline import load

if TYPE_CHECKING:
    from lib.contracts import LLM


def _degenerate(text: str) -> tuple[str, str]:
    return "What does this passage describe?", text[:200]


def _via_llm(llm: "LLM", text: str) -> tuple[str, str]:
    prompt = (
        "From the passage, write one factual question and its answer.\n"
        "Format exactly:\nQ: <question>\nA: <answer>\n\nPassage:\n" + text
    )
    out = llm.chat([Message("user", prompt)]).text
    question, answer = "", ""
    for line in out.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("q:"):
            question = stripped[2:].strip()
        elif stripped.lower().startswith("a:"):
            answer = stripped[2:].strip()
    return (question or "What does this passage describe?"), (answer or text[:200])


def generate(corpus: str, n: int = 10, llm: "LLM | None" = None) -> list[EvalRow]:
    rows = []
    for chunk in load(corpus)[:n]:
        question, ground_truth = _via_llm(llm, chunk.text) if llm else _degenerate(chunk.text)
        rows.append(EvalRow(question=question, ground_truth=ground_truth))
    return rows
