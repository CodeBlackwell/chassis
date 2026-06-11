"""End-to-end smoke gate. Runs the real pipeline through the configured stack.

  python scripts/smoke.py --stage ingest --corpus <folder> [--profile memory]
  python scripts/smoke.py --stage e2e    --corpus <folder> [--query "..."]

ingest: load -> chunk -> embed -> upsert -> search.
e2e:    ingest, then route -> retrieve -> guardrail -> Answer through the
        orchestrator. With the `memory` profile both run with no keys, services,
        or heavy deps (the orchestrator falls back to extractive answers).
"""

import argparse
import sys
import uuid

from config.settings import Settings
from lib.ingestion.pipeline import ingest
from lib.trace import TraceBus


def _build(profile, corpus, bus):
    settings = Settings.load(profile)
    embedder = settings.build("embedder")
    store = settings.build("vectorstore")
    ing = settings.layers.get("ingestion", {})
    chunks = ingest(
        corpus, embedder, store, trace=bus,
        chunk_size=ing.get("chunk_size", 800), overlap=ing.get("overlap", 120),
    )
    return settings, embedder, store, chunks


def ingest_stage(corpus, profile=None, query="overview"):
    bus = TraceBus(run_id=uuid.uuid4().hex[:8])
    settings, embedder, store, chunks = _build(profile, corpus, bus)
    retriever = settings.build("retriever", embedder=embedder, store=store)
    hits = retriever.retrieve(query, k=3)
    bus.emit("smoke", "done", chunks=len(chunks), hits=len(hits))
    return chunks, hits, bus


def e2e_stage(corpus, profile=None, query="What is this about?"):
    bus = TraceBus(run_id=uuid.uuid4().hex[:8])
    settings, embedder, store, chunks = _build(profile, corpus, bus)
    orchestrator = settings.build(
        "orchestrator",
        retriever=settings.build("retriever", embedder=embedder, store=store),
        memory=settings.build("memory", embedder=embedder, store=store),
        guardrail=settings.build("guardrail"),
        trace=bus,
    )
    return chunks, orchestrator.handle(query), bus


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["ingest", "e2e"], default="ingest")
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--query", default=None)
    args = parser.parse_args()

    if args.stage == "ingest":
        chunks, hits, bus = ingest_stage(args.corpus, args.profile, args.query or "overview")
        if not chunks or not hits:
            print("FAIL: nothing ingested or no hits", file=sys.stderr)
            sys.exit(1)
        print(f"OK: ingested {len(chunks)} chunks; search returned {len(hits)} hits")
    else:
        query = args.query or "What is this about?"
        chunks, answer, bus = e2e_stage(args.corpus, args.profile, query)
        if not chunks or not answer.text:
            print("FAIL: nothing ingested or empty answer", file=sys.stderr)
            sys.exit(1)
        print(f"OK: {len(chunks)} chunks; route={answer.route}; {len(answer.citations)} citations")
        print(f"answer: {answer.text[:120]!r}")
    print(f"trace -> {bus.path}")


if __name__ == "__main__":
    main()
