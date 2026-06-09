"""RAGAS-style metrics, lexical proxies so they score with no LLM or embedder.
Each returns a float in [0,1]. A real embedder/LLM raises fidelity; these are the
honest, explainable baseline.

- faithfulness: fraction of the answer grounded in the contexts (catches fabrication)
- answer_relevance: fraction of the question addressed by the answer (catches dodging)
- context_precision: fraction of retrieved contexts relevant to the truth (catches
  retrieval garbage)
"""

import re
from collections.abc import Sequence

_WORD = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def faithfulness(answer: str, contexts: Sequence[str]) -> float:
    answer_tokens = _tokens(answer)
    if not answer_tokens:
        return 0.0
    context_tokens: set[str] = set().union(*(_tokens(c) for c in contexts)) if contexts else set()
    return len(answer_tokens & context_tokens) / len(answer_tokens)


def answer_relevance(answer: str, question: str) -> float:
    question_tokens = _tokens(question)
    if not question_tokens:
        return 0.0
    return len(question_tokens & _tokens(answer)) / len(question_tokens)


def context_precision(
    contexts: Sequence[str], ground_truth: str, min_overlap: float = 0.1
) -> float:
    if not contexts:
        return 0.0
    truth_tokens = _tokens(ground_truth)
    if not truth_tokens:
        return 0.0
    relevant = sum(
        1
        for c in contexts
        if len(_tokens(c) & truth_tokens) / len(truth_tokens) >= min_overlap
    )
    return relevant / len(contexts)
