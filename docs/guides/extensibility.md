# Extensibility

CHASSIS is built to be extended and re-skinned, not edited. The same three primitives — **contract, registry entry, profile** — cover every kind of change. This doc walks the four moves you will actually make.

> Note: `registry.py`, `config/settings.py`, the adapter packages, and `config/profiles/*.yaml` are deferred to a later pass. The shapes below are the target they are built against, and match the frozen `lib/contracts.py`.

## The flexibility model

| Primitive | Lives in | Job |
|-----------|----------|-----|
| Contract | `lib/contracts.py` | the Protocol an adapter must satisfy |
| Adapter | `lib/*/`, `app/*/` | one concrete implementation of a contract |
| Registry entry | `lib/registry.py` | maps a config string to an adapter class |
| Profile | `config/profiles/*.yaml` | names a whole stack of choices |

The rule: **nothing imports a concrete class directly.** Code depends on the contract; the registry resolves the concrete class from config at startup. That single indirection is what makes every layer swappable.

## Move 1 — Add an adapter (the common case)

Say you want a new vector store, `LanceDB`. Three edits, no other file touched.

1. **Implement the contract.** Create `lib/vectorstore/lance_store.py` with a class that satisfies the `VectorStore` Protocol from `lib/contracts.py`:

   ```python
   from typing import Sequence
   from lib.contracts import Chunk, SearchResult

   class LanceStore:
       def ensure_collection(self, name: str, dim: int) -> None: ...
       def upsert(self, collection: str, chunks: Sequence[Chunk],
                  vectors: Sequence[list[float]]) -> None: ...
       def search(self, collection: str, vector: list[float],
                  k: int = 5) -> list[SearchResult]: ...
   ```

   No base class to inherit — Protocols are structural. If the methods match, it fits.

2. **Register it.** Add one line to `REGISTRY["vectorstore"]` in `lib/registry.py`:

   ```python
   "lance": "lib.vectorstore.lance_store:LanceStore",
   ```

3. **Select it.** Reference it in a profile or via an env override:

   ```yaml
   vectorstore: {impl: lance, uri: "./data/lance"}
   ```

Done. The orchestrator, retriever, and UI never learn the name "Lance" — they only ever see the `VectorStore` contract. The same recipe adds an LLM provider (`lib/llm/`), an embedder (`lib/embeddings/`), or any other layer.

## Move 2 — Add a whole new layer

When a project needs a capability no contract covers yet (say, a `Reranker` between retrieval and synthesis):

1. **Define the Protocol** in `lib/contracts.py` (and any shared dataclasses it needs).
2. **Add a registry slot** — a new top-level key in `REGISTRY` (e.g. `"reranker"`).
3. **Write adapters** under a new package (`lib/reranker/`) and wire it into the orchestrator loop against the new contract.

**When this is allowed:** before the contracts are frozen for a build, or as a deliberate, isolated change between builds. **When it is not:** mid-build, while parallel work depends on the current contracts. A new layer changes the shared surface, and changing the shared surface mid-build is how parallel work collides. If you discover a missing layer mid-build, log it and work around it; add it cleanly afterward.

## Move 3 — Add a profile

A profile is a named stack — the fastest way to flip an entire backend.

1. Copy an existing `config/profiles/*.yaml`.
2. Change the `impl` fields (and their kwargs) to the stack you want.
3. Select it with `CHASSIS_PROFILE=<name>`.

```yaml
# config/profiles/chroma-inmem.yaml
llm:          {impl: anthropic, model: claude-sonnet-4-6}
embedder:     {impl: minilm, model: sentence-transformers/all-MiniLM-L6-v2}
vectorstore:  {impl: chroma}          # in-process, no service
retriever:    {impl: simple}
memory:       {impl: buffer, window: 8, recall_k: 3}
guardrail:    {impl: passthrough}   # unopinionated stub; implement per project
orchestrator: {impl: default, k: 5}
evaluator:    {impl: ragas}
```

**The live-pivot mechanism.** `settings.py` resolves the profile first, then lets individual env vars override any layer:

```bash
CHASSIS_LLM_IMPL=ollama   # one var flips the whole system to local Ollama
```

This is the single override path that turns a dead cloud key into a one-line recovery — no file edits, no restart of anything but the app. (See the embedder-dim coupling below before overriding the embedder after ingest.)

## Move 4 — Re-skin CHASSIS into a new project

The whole point: a new domain reuses the base and writes only what is genuinely domain-specific.

Checklist:

1. **Pick a profile** (or write one) for the target environment — keys available, compute available, services allowed.
2. **Write the project's loader.** CHASSIS ships no ingestion pipeline — produce `Chunk`s from the corpus however fits the domain (see [stack-matrix.md](../reference/stack-matrix.md), Ingestion), then `embedder.embed` → `store.upsert` through the contracts.
3. **Implement domain specialists** in `app/orchestration/` against the `Retriever`, `Memory`, and `Guardrail` contracts. This is usually the only real code a new project writes.
4. **Tune, don't rebuild.** Per-stack knobs live in the profile (`k`, `window`, `recall_k`); the code-level defaults behind them — and the rest of the tunable ints/strings (LLM token budgets, collection names, eval thresholds, ports) — are centralized in `config/defaults.py`.
5. **Reuse everything else** — trace bus, registry, eval harness, UI tabs, deployment — unchanged.

If a new project finds itself editing `lib/`, that is a signal to add an adapter (Move 1) or a layer (Move 2), not to fork the base.

## Rules of engagement

- **Contracts are frozen before a build.** Adapters and app layers code against them and never propose changes mid-build.
- **Complaints are logged, not patched.** If an implementation believes a contract is wrong, it records the issue and works around it; the contract is revisited between builds.
- **Path ownership.** Each layer owns its directory. An adapter edits only its own package plus its one-line registry entry. Cross-package edits during a parallel build are reverted — that is the cheap insurance contracts alone cannot provide.
- **Mind the two couplings** (see [architecture.md](../architecture/architecture.md)): vector-DB choice drives deployment, and embedder dimension is frozen at ingest. Everything else is freely swappable.
