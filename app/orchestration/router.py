"""Query router: classify into the three handler classes. Heuristic by default
(deterministic, offline). chitchat is answered directly by the orchestrator;
synthesis and retrieval both go through the retriever.
"""

import re

_CHITCHAT = re.compile(
    r"^\s*(hi|hello|hey|yo|thanks|thank you|how are you|good (morning|afternoon|evening))\b",
    re.I,
)
_SYNTHESIS = re.compile(
    r"\b(compare|compari\w+|summari[sz]e|summary|overview|explain|relationship|"
    r"differences?|across|versus|vs\.?|trade[- ]?offs?)\b",
    re.I,
)


def route(query: str) -> str:
    if _CHITCHAT.search(query):
        return "chitchat"
    if _SYNTHESIS.search(query):
        return "synthesis"
    return "retrieval"
