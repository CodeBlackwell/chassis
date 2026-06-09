"""End-to-end smoke gate. Runs the real pipeline through the configured stack.

  python scripts/smoke.py --stage ingest --corpus <folder> [--profile memory]

ingest: load -> chunk -> embed -> upsert -> search, emitting trace events. With
the `memory` profile this needs no keys, services, or heavy deps.
"""

import argparse
import sys
import uuid

from config.settings import Settings
from lib.ingestion.pipeline import ingest
from lib.retriever import SimpleRetriever
from lib.trace import TraceBus


def ingest_stage(corpus: str, profile: str | None = None, query: str = "overview"):
    settings = Settings.load(profile)
    embedder = settings.build("embedder")
    store = settings.build("vectorstore")
    ing = settings.layers.get("ingestion", {})
    bus = TraceBus(run_id=uuid.uuid4().hex[:8])
    chunks = ingest(
        corpus,
        embedder,
        store,
        trace=bus,
        chunk_size=ing.get("chunk_size", 800),
        overlap=ing.get("overlap", 120),
    )
    hits = SimpleRetriever(embedder, store).retrieve(query, k=3)
    bus.emit("smoke", "done", chunks=len(chunks), hits=len(hits))
    return chunks, hits, bus


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["ingest", "e2e"], default="ingest")
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--profile", default=None)
    args = parser.parse_args()

    if args.stage != "ingest":
        print("e2e stage not implemented yet (needs orchestration)", file=sys.stderr)
        sys.exit(1)

    chunks, hits, bus = ingest_stage(args.corpus, args.profile)
    if not chunks:
        print(f"FAIL: no chunks ingested from {args.corpus}", file=sys.stderr)
        sys.exit(1)
    if not hits:
        print("FAIL: search returned no hits", file=sys.stderr)
        sys.exit(1)
    print(f"OK: ingested {len(chunks)} chunks; search returned {len(hits)} hits")
    print(f"trace -> {bus.path}")


if __name__ == "__main__":
    main()
