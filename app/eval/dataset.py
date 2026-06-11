"""Corpus-agnostic seed-set generation: turn chunks into (question, ground_truth)
EvalRows. With an LLM the system writes its own exam; without one, a degenerate
fallback keeps it offline. Producing the chunks is the project's loading decision
(see docs/reference/stack-matrix.md, Ingestion).
"""

from typing import TYPE_CHECKING

from config import defaults
from lib.contracts import Chunk, EvalRow, Message

if TYPE_CHECKING:
    from lib.contracts import LLM


def _degenerate(text: str) -> tuple[str, str]:
    return "What does this passage describe?", text[: defaults.GROUND_TRUTH_CHARS]


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
    truth = answer or text[: defaults.GROUND_TRUTH_CHARS]
    return (question or "What does this passage describe?"), truth


def generate(
    chunks: list[Chunk], n: int = defaults.EVAL_SEED_N, llm: "LLM | None" = None
) -> list[EvalRow]:
    rows = []
    for chunk in chunks[:n]:
        question, ground_truth = _via_llm(llm, chunk.text) if llm else _degenerate(chunk.text)
        rows.append(EvalRow(question=question, ground_truth=ground_truth))
    return rows
