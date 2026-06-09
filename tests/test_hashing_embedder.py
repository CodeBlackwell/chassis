import math

from lib.embeddings.hashing import HashingEmbedder


def test_dim_and_shape():
    emb = HashingEmbedder(dim=64)
    vecs = emb.embed(["hello world", "another doc"])
    assert emb.dim == 64
    assert len(vecs) == 2
    assert all(len(v) == 64 for v in vecs)


def test_deterministic():
    emb = HashingEmbedder(dim=64)
    assert emb.embed(["repeatable text"]) == emb.embed(["repeatable text"])


def test_normalized():
    [vec] = HashingEmbedder(dim=64).embed(["some tokens here please"])
    assert math.isclose(math.sqrt(sum(x * x for x in vec)), 1.0, rel_tol=1e-6)


def test_empty_text_is_zero_vector():
    [vec] = HashingEmbedder(dim=32).embed(["!!! ???"])  # no word tokens
    assert vec == [0.0] * 32


def test_lexical_overlap_scores_higher():
    emb = HashingEmbedder(dim=512)
    q, related, unrelated = emb.embed(
        ["database migration", "the database migration plan", "ocean weather report"]
    )

    def cos(a, b):
        return sum(x * y for x, y in zip(a, b, strict=True))

    assert cos(q, related) > cos(q, unrelated)
