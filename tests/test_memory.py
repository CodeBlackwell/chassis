from collections.abc import Sequence

from app.memory.buffer import BufferMemory
from lib.contracts import LLMResponse, Message, Turn
from lib.embeddings.hashing import HashingEmbedder
from lib.vectorstore.memory_store import MemoryStore


class FakeLLM:
    def __init__(self, text: str = "SUMMARY") -> None:
        self._text = text

    def chat(self, messages: Sequence[Message], *, temperature=0.0, max_tokens=1024) -> LLMResponse:
        return LLMResponse(text=self._text, model="fake")


def _mem(**kw) -> BufferMemory:
    return BufferMemory(HashingEmbedder(dim=512), MemoryStore(), **kw)


def _turn(content: str, i: int = 0) -> Turn:
    return Turn(role="user", content=content, ts=float(i))


def test_window_keeps_last_n():
    mem = _mem(window=8)
    for i in range(10):
        mem.add(_turn(f"message number {i}", i))
    recent = mem.context("").recent
    assert len(recent) == 8
    assert recent[0].content == "message number 2"
    assert recent[-1].content == "message number 9"


def test_long_term_recall_after_eviction():
    mem = _mem(window=4, recall_k=3)
    mem.add(_turn("the secret passphrase is plum jelly avalanche", 0))
    for i in range(1, 20):
        mem.add(_turn(f"unrelated chatter about weather on day {i}", i))
    recalled = mem.context("secret passphrase plum jelly").recalled
    assert any("plum jelly" in r.chunk.text for r in recalled)


def test_empty_query_skips_recall():
    mem = _mem()
    mem.add(_turn("hello", 0))
    assert mem.context("").recalled == []


def test_overflow_summary_without_llm():
    mem = _mem(window=2)
    for i in range(4):
        mem.add(_turn(f"turn {i}", i))
    summary = mem.context("").summary
    assert summary is not None
    assert "turn 0" in summary and "turn 1" in summary


def test_overflow_summary_with_llm():
    mem = _mem(window=2, llm=FakeLLM("CONDENSED"))
    for i in range(4):
        mem.add(_turn(f"turn {i}", i))
    assert mem.context("").summary == "CONDENSED"


def test_no_overflow_no_summary():
    mem = _mem(window=8)
    mem.add(_turn("only one", 0))
    assert mem.context("").summary is None
