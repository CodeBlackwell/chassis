"""Glue: run seed questions through an orchestrator to fill answer + contexts, then
render a metrics report. Keeps the orchestrator dependency out of the evaluator.
"""

from collections.abc import Sequence
from dataclasses import replace
from typing import TYPE_CHECKING

from lib.contracts import EvalRow

from app.eval.evaluator import summary

if TYPE_CHECKING:
    from lib.contracts import Orchestrator


def answer_rows(orchestrator: "Orchestrator", rows: Sequence[EvalRow]) -> list[EvalRow]:
    filled = []
    for row in rows:
        answer = orchestrator.handle(row.question)
        filled.append(replace(row, answer=answer.text, contexts=answer.contexts))
    return filled


def report(rows: Sequence[EvalRow]) -> str:
    return "\n".join(f"{k:20s} {v:.3f}" for k, v in summary(rows).items())
