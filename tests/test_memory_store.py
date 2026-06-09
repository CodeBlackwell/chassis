from lib.contracts import Chunk
from lib.vectorstore.memory_store import MemoryStore


def _chunk(cid, text):
    return Chunk(id=cid, text=text, source="src")


def test_upsert_and_search_ranks_by_cosine():
    store = MemoryStore()
    store.ensure_collection("c", dim=3)
    store.upsert(
        "c",
        [_chunk("a", "a"), _chunk("b", "b")],
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
    )
    hits = store.search("c", [1.0, 0.0, 0.0], k=2)
    assert [h.chunk.id for h in hits] == ["a", "b"]
    assert hits[0].score > hits[1].score


def test_k_limits_results():
    store = MemoryStore()
    store.upsert("c", [_chunk(str(i), "x") for i in range(5)], [[1.0]] * 5)
    assert len(store.search("c", [1.0], k=2)) == 2


def test_upsert_dedupes_by_id():
    store = MemoryStore()
    store.upsert("c", [_chunk("a", "v1")], [[1.0, 0.0]])
    store.upsert("c", [_chunk("a", "v2")], [[0.0, 1.0]])
    hits = store.search("c", [0.0, 1.0], k=5)
    assert len(hits) == 1
    assert hits[0].chunk.text == "v2"


def test_search_missing_collection_returns_empty():
    assert MemoryStore().search("nope", [1.0]) == []
