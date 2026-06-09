"""Pure guardrail checks: each returns (passed, reason[s]) with no side effects, so
they compose and test cleanly. Injection heuristics are named after real attack
classes (OWASP LLM01-style), so the input rail can say exactly what it blocked.
"""

import re
from collections.abc import Sequence

MAX_INPUT_CHARS = 16_000

# (attack_class, pattern). Multiple patterns may map to one class.
_INJECTION: list[tuple[str, re.Pattern[str]]] = [
    ("system_prompt_override", re.compile(
        r"ignore\s+(all\s+|the\s+)?(previous|prior|above|earlier)\s+(instruction|prompt)", re.I)),
    ("system_prompt_override", re.compile(
        r"disregard\s+(your\s+)?(system\s+)?(prompt|instruction)", re.I)),
    ("role_injection", re.compile(r"\byou\s+are\s+now\b", re.I)),
    ("role_injection", re.compile(r"\bact\s+as\b|\bpretend\s+to\s+be\b", re.I)),
    ("authority_escalation", re.compile(
        r"\b(?:i\s+am|as)\s+(?:an?\s+|the\s+)?(?:system\s+)?"
        r"(?:administrator|admin|root|superuser)\b", re.I)),
    ("hypothetical_jailbreak", re.compile(
        r"\b(hypothetically|imagine that|suppose that|pretend that)\b.*"
        r"\b(ignore|bypass|without)\b", re.I)),
    ("context_escape", re.compile(r"</?(system|instruction|prompt)s?>", re.I)),
]

_PII: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")),
    ("phone", re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")),
    ("api_key", re.compile(
        r"(?:sk|pk|api[_-]?key|token|secret|bearer)[-_]?[a-zA-Z0-9]{16,}", re.I)),
]

_WORD = re.compile(r"[a-z0-9]+")


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def check_length(text: str, max_chars: int = MAX_INPUT_CHARS) -> tuple[bool, str | None]:
    if len(text) > max_chars:
        return False, f"length:exceeds_{max_chars}"
    return True, None


def check_injection(text: str) -> tuple[bool, list[str]]:
    hits = [f"injection:{name}" for name, pat in _INJECTION if pat.search(text)]
    reasons = _unique(hits)
    return (not reasons), reasons


def check_pii(text: str) -> tuple[bool, list[str]]:
    hits = [f"pii:{name}" for name, pat in _PII if pat.search(text)]
    reasons = _unique(hits)
    return (not reasons), reasons


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


def check_grounded(
    answer: str, contexts: Sequence[str], min_overlap: float = 0.3
) -> tuple[bool, str | None]:
    answer_tokens = _tokens(answer)
    context_tokens: set[str] = set().union(*(_tokens(c) for c in contexts)) if contexts else set()
    if not answer_tokens or not context_tokens:
        return True, None  # nothing to ground against; emptiness handled elsewhere
    overlap = len(answer_tokens & context_tokens) / len(answer_tokens)
    if overlap < min_overlap:
        return False, f"ungrounded:overlap_{overlap:.2f}"
    return True, None
