"""Pure formatters: turn contract objects into table rows for the dashboard. No
Gradio import, so the UI's data shaping tests offline.
"""

import json
from collections.abc import Sequence

from lib.contracts import Answer, EvalRow, TraceEvent

TRACE_HEADERS = ["ts", "component", "event", "payload"]
SOURCE_HEADERS = ["chunk", "text"]
GUARDRAIL_HEADERS = ["ts", "stage", "passed", "reasons"]
EVAL_BASE_HEADERS = ["question", "answer"]


def trace_rows(events: Sequence[TraceEvent]) -> list[list[str]]:
    return [[f"{e.ts:.2f}", e.component, e.event, json.dumps(e.payload)] for e in events]


def guardrail_rows(events: Sequence[TraceEvent]) -> list[list[str]]:
    rows = []
    for e in events:
        if e.component.startswith("guardrail"):
            reasons = ", ".join(e.payload.get("reasons", []))
            rows.append([f"{e.ts:.2f}", e.component, str(e.payload.get("passed", "")), reasons])
    return rows


def source_rows(answer: Answer) -> list[list[str]]:
    return [
        [cid, text[:160]] for cid, text in zip(answer.citations, answer.contexts, strict=False)
    ]


def eval_table(rows: Sequence[EvalRow]) -> tuple[list[str], list[list[str]]]:
    # columns come from the score dicts, so any Evaluator's metrics render
    keys = sorted({k for r in rows for k in r.scores})
    data = [
        [r.question, (r.answer or "")[:80], *(f"{r.scores.get(k, 0.0):.2f}" for k in keys)]
        for r in rows
    ]
    return [*EVAL_BASE_HEADERS, *keys], data
