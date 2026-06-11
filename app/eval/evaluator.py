"""RagasEvaluator: fills each row's scores dict with the metrics and (if an LLM is
given) an LLM-as-judge score. Satisfies the Evaluator contract.

Honest caveat to volunteer: LLM-generated ground truth plus an LLM judge is
self-grading with correlated errors; production would use human-labeled goldens.
"""

import csv
import re
from collections.abc import Sequence
from dataclasses import replace
from typing import TYPE_CHECKING

from config import defaults
from lib.contracts import EvalRow, Message

from app.eval import metrics

if TYPE_CHECKING:
    from lib.contracts import LLM


def _parse_float(text: str) -> float:
    match = re.search(r"[01](?:\.\d+)?", text)
    return min(max(float(match.group()), 0.0), 1.0) if match else 0.0


class RagasEvaluator:
    def __init__(self, llm: "LLM | None" = None) -> None:
        self._llm = llm

    def run(self, rows: Sequence[EvalRow]) -> list[EvalRow]:
        return [self._score(row) for row in rows]

    def _score(self, row: EvalRow) -> EvalRow:
        answer = row.answer or ""
        scores = dict(row.scores)
        scores["faithfulness"] = metrics.faithfulness(answer, row.contexts)
        scores["answer_relevance"] = metrics.answer_relevance(answer, row.question)
        scores["context_precision"] = metrics.context_precision(row.contexts, row.ground_truth)
        if self._llm is not None:
            scores["judge"] = self._judge(row)
        return replace(row, scores=scores)

    def _judge(self, row: EvalRow) -> float:
        assert self._llm is not None
        prompt = (
            "Rate from 0 to 1 how well the answer addresses the question given the "
            "context. Reply with only the number.\n\n"
            f"Question: {row.question}\nAnswer: {row.answer or ''}\n"
            f"Context:\n{chr(10).join(row.contexts)}"
        )
        judged = self._llm.chat([Message("user", prompt)], max_tokens=defaults.JUDGE_MAX_TOKENS)
        return _parse_float(judged.text)


def summary(rows: Sequence[EvalRow]) -> dict[str, float]:
    keys = sorted({k for row in rows for k in row.scores})
    if not rows:
        return {}
    return {k: sum(row.scores.get(k, 0.0) for row in rows) / len(rows) for k in keys}


def to_csv(rows: Sequence[EvalRow], path: str) -> None:
    keys = sorted({k for row in rows for k in row.scores})
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["question", "answer", *keys])
        for row in rows:
            writer.writerow(
                [row.question, row.answer or "", *(f"{row.scores.get(k, 0.0):.3f}" for k in keys)]
            )


if TYPE_CHECKING:
    from lib.contracts import Evaluator

    _conforms: type[Evaluator] = RagasEvaluator
