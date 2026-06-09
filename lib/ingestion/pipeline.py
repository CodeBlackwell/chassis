"""Corpus-agnostic ingestion: a runtime folder path -> chunked, embedded, upserted
vectors. Handles .md/.txt (read) and .pdf (pypdf, lazy). The domain is never baked
in; you point it at a folder at runtime.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from lib.contracts import Chunk

if TYPE_CHECKING:
    from lib.contracts import Embedder, VectorStore
    from lib.trace import TraceBus

_SUFFIXES = {".md", ".txt", ".pdf"}


def _read(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def _chunk(text: str, size: int, overlap: int) -> list[str]:
    step = max(size - overlap, 1)
    pieces = [text[i : i + size] for i in range(0, len(text), step)]
    return [p for p in pieces if p.strip()]


def load(folder: str, *, chunk_size: int = 800, overlap: int = 120) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(Path(folder).rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _SUFFIXES:
            continue
        for i, piece in enumerate(_chunk(_read(path), chunk_size, overlap)):
            chunks.append(Chunk(id=f"{path}:{i}", text=piece, source=str(path)))
    return chunks


def ingest(
    folder: str,
    embedder: "Embedder",
    store: "VectorStore",
    *,
    collection: str = "chassis",
    chunk_size: int = 800,
    overlap: int = 120,
    trace: "TraceBus | None" = None,
) -> list[Chunk]:
    chunks = load(folder, chunk_size=chunk_size, overlap=overlap)
    sources = {c.source for c in chunks}
    if trace:
        trace.emit("ingestion", "load", files=len(sources), chunks=len(chunks))
    if not chunks:
        return chunks
    vectors: Sequence[list[float]] = embedder.embed([c.text for c in chunks])
    store.ensure_collection(collection, embedder.dim)
    store.upsert(collection, chunks, vectors)
    if trace:
        trace.emit("ingestion", "upsert", collection=collection, count=len(chunks))
    return chunks
