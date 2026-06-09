from lib.embeddings.hashing import HashingEmbedder
from lib.ingestion.pipeline import _chunk, ingest, load
from lib.retriever import SimpleRetriever
from lib.trace import TraceBus
from lib.vectorstore.memory_store import MemoryStore


def _corpus(tmp_path):
    (tmp_path / "a.md").write_text("database migration plan and schema changes")
    (tmp_path / "b.txt").write_text("ocean weather report and tide tables")
    (tmp_path / "ignore.bin").write_bytes(b"\x00\x01")
    return str(tmp_path)


def test_chunk_respects_size_and_overlap():
    pieces = _chunk("abcdefghij", size=4, overlap=1)
    assert pieces[0] == "abcd"
    assert pieces[1] == "defg"  # step = size - overlap = 3


def test_load_only_supported_files(tmp_path):
    chunks = load(_corpus(tmp_path))
    sources = {c.source.rsplit("/", 1)[-1] for c in chunks}
    assert sources == {"a.md", "b.txt"}


def test_ingest_then_retrieve_finds_right_doc(tmp_path):
    corpus = _corpus(tmp_path)
    embedder, store = HashingEmbedder(dim=512), MemoryStore()
    bus = TraceBus("ing", runs_dir=str(tmp_path / "runs"))
    chunks = ingest(corpus, embedder, store, trace=bus)
    assert len(chunks) == 2

    hits = SimpleRetriever(embedder, store).retrieve("database schema migration", k=1)
    assert hits and hits[0].chunk.source.endswith("a.md")

    events = {e.event for e in bus.recent(component_prefix="ingestion")}
    assert events == {"load", "upsert"}


def test_ingest_empty_folder_no_crash(tmp_path):
    chunks = ingest(str(tmp_path), HashingEmbedder(), MemoryStore())
    assert chunks == []
