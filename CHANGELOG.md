# Changelog

All notable changes to CHASSIS. Format follows [Keep a Changelog](https://keepachangelog.com/); this project is pre-1.0 and not yet versioned.

## [Unreleased]

### Added

- **Repo skeleton + frozen contracts.** Flat `lib/`/`app/`/`config/` layout; `lib/contracts.py` with all shared dataclasses (`Message`, `LLMResponse`, `Chunk`, `SearchResult`, `Turn`, `MemoryContext`, `Verdict`, `EvalRow`, `Answer`, `TraceEvent`) and Protocols (`LLM`, `Embedder`, `VectorStore`, `Retriever`, `Orchestrator`, `Memory`, `Guardrail`, `Evaluator`). Imports clean, `mypy` clean.
- **Hygiene.** `pyproject.toml` (hatchling, ruff line-length 100, mypy, zero runtime deps), `.gitignore`, MIT `LICENSE`, `README.md`, `.env.example`.
- **Core docs.** `docs/architecture.md` (flexibility mechanism, trace bus, query flow, the two couplings), `docs/extensibility.md` (add adapter/layer/profile, re-skin guide), `docs/stack-matrix.md` (per-layer pro/cons matrix).
- **Workspace recon.** `docs/2026-06-09_workspace-recon-injection-plan.md` — eight read-only sweeps across the BLACKBOX workspace mapping battle-tested patterns to CHASSIS seams (default/option/deferred/YAGNI).
- **Stack-matrix layers.** Added a Retrieval layer (vector-only default + Hybrid graph-RAG option behind the `Retriever` contract) and a Theming layer (`tokens.json` → Gradio CSS injection, METHODPROOF default).
- **Project docs.** `CLAUDE.md` (hub), `ROADMAP.md`, this `CHANGELOG.md`.
- **Knowledge-graph contract (the one sanctioned pre-build addition).** `GraphNode`, `GraphEdge` dataclasses + a `GraphStore` Protocol (`upsert`, `neighbors`) in `lib/contracts.py`, enabling a future `HybridRetriever` (vector hit → graph-expand) behind the existing `Retriever` contract. No existing Protocol changed.

- **Wave 0 core — the flexibility engine + trace bus.**
  - `lib/registry.py`: `build(layer, name, **kwargs)` lazy-importlib factory + the full REGISTRY map (llm / embedder / vectorstore / graphstore). Referencing an unwritten adapter is fine until something builds it.
  - `config/settings.py`: `Settings.load(profile)` resolves a profile YAML then applies `CHASSIS_<LAYER>_IMPL` env overrides (the live-pivot path); `.build(layer)` ties settings to the registry.
  - `config/profiles/`: `qdrant-local`, `chroma-inmem`, `faiss-bare`.
  - `lib/trace.py`: `TraceBus` — `deque(maxlen=500)` behind a lock + per-run JSONL sink; `emit()` and `recent(component_prefix=)`.
  - Runtime deps added: `pyyaml`, `python-dotenv`. 13 offline tests; mypy + ruff clean.
- **LLM + embedder adapters.**
  - `lib/llm/`: `AnthropicLLM`, `OpenAILLM` (lazy SDK import; pure message-split + response-shape helpers), `OllamaLLM` (stdlib `urllib`, zero extra deps — the no-key offline fallback). All satisfy the `LLM` contract (TYPE_CHECKING conformance guard).
  - `lib/embeddings/`: `SbertEmbedder` (serves `minilm` + `bge`; lazy model load) and `OpenAIEmbedder` (1536-dim fixed at construction). Both satisfy `Embedder`.
  - Adapter deps are now `[project.optional-dependencies]` groups (`llm-anthropic`, `llm-openai`, `embeddings-sbert`, `embeddings-openai`) so the base install stays light; install only the stack a profile selects.
  - 9 more offline tests (helper shaping + Settings→registry→real-adapter wiring proven for the zero-dep path). Real round-trips need keys/models (deferred). 22 tests total.
- **Vector stores + ingestion + the first real smoke gate.**
  - `lib/vectorstore/`: `MemoryStore` (zero-dep brute-force cosine), `FaissStore`, `ChromaStore`, `QdrantStore` — all satisfy `VectorStore` (conformance-guarded; heavy backends lazy-imported).
  - `lib/embeddings/hashing.py`: `HashingEmbedder` — zero-dep feature-hashing (real lexical signal), for tests/CI/offline.
  - `lib/ingestion/pipeline.py`: `load()` (.md/.txt/.pdf → chunks with size/overlap) + `ingest()` (embed → ensure_collection → upsert, emitting trace events).
  - `lib/retriever.py`: `SimpleRetriever` (embed query → store search), satisfies `Retriever`.
  - `scripts/smoke.py --stage ingest`: runs the real pipeline through the configured stack; the `memory` profile makes it pass with **zero keys/services/heavy deps**.
  - `config/profiles/memory.yaml`; registry gains `embedder: hashing` and `vectorstore: memory`; `[project.optional-dependencies]` for qdrant/chroma/faiss/ingestion.
  - 13 more offline tests + a real end-to-end smoke run; 35 tests total. mypy + ruff clean.
- **Docker + justfile (deployment scaffolding).**
  - `Dockerfile` (uv, non-root, `EXTRAS` build arg installs only the profile's adapters), `.dockerignore`, `docker-compose.yml` (Qdrant + app, dev), `docker-compose.prod.yml` (internal network, Caddy as sole public entrypoint), `Caddyfile`.
  - `justfile`: house recipe set (`default`/`setup`/`test`/`lint`/`fix`/`ingest`/`smoke`/`services`/`down`/`dev`/`build`/`deploy`/`logs`/`clean`); `dotenv-load`, env-driven deploy host/dir, port-kill before `dev`.
  - Both compose files validate (`docker compose config`); `just --list` + `just ingest` run. The app server CMD (`app.ui`) goes live with the Wave 2 dashboard.
  - Qdrant URL now comes from `QDRANT_URL` env (not baked in the profile) so the in-container hostname wires correctly.

- **Wave 1 — Guardrails layer.**
  - `app/guardrails/checks.py`: pure `(passed, reason)` checks — length cap, **named** prompt-injection classes (system-prompt override, role injection, authority escalation, hypothetical jailbreak, context escape), PII regexes (email/phone/api-key), and lexical grounding.
  - `app/guardrails/guard.py`: `DefaultGuardrail` (satisfies `Guardrail`) — refuse-by-default input rail, non-empty + grounded output rail, plus an optional LLM safety judge. Deterministic without an LLM, so it tests fully offline.
  - 9 tests (each attack class blocked, benign passes, PII/length blocks, grounding, judge safe/unsafe via a fake LLM); 44 total. mypy + ruff clean.

### Notes

- Contracts are **re-frozen** as of the `GraphStore` addition (2026-06-09). No further changes in flight; future extension happens via adapters, not contract edits.
- Deferred to later passes: `lib/registry.py`, `lib/trace.py`, `config/settings.py`, all adapters, `lib/ingestion/`, every `app/*` layer, `scripts/`, the Ralph harness, `docker-compose`/`Dockerfile`/`justfile`, and `tests/`.
