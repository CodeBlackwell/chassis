"""Zero-dependency feature-hashing embedder. Hashes word tokens into a fixed-dim
vector (the hashing trick), L2-normalized. Deterministic, no model download, no
torch — for tests, CI, and offline use. Captures lexical overlap, not semantics,
so use a real model (sbert/openai) for quality retrieval.
"""

import hashlib
import math
import re
from collections.abc import Sequence
from typing import TYPE_CHECKING

from config import defaults

_TOKEN = re.compile(r"[a-z0-9]+")


class HashingEmbedder:
    def __init__(self, dim: int = defaults.HASHING_DIM) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for token in _TOKEN.findall(text.lower()):
            digest = hashlib.md5(token.encode()).digest()
            vec[int.from_bytes(digest[:4], "little") % self._dim] += 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec] if norm else vec


if TYPE_CHECKING:
    from lib.contracts import Embedder

    _conforms: type[Embedder] = HashingEmbedder
