# Roadmap

Build order for CHASSIS, by wave and layer. No dates — the workspace builds fast. Each section lists **Done**, **Needed**, and **Notes**. Source of truth for *what* each layer must satisfy is `lib/contracts.py`; source for *which option is default* is [docs/stack-matrix.md](docs/stack-matrix.md); source for *which workspace pattern to copy* is the [recon plan](docs/2026-06-09_workspace-recon-injection-plan.md).

## Wave 0 — Foundation (the pre-bakeable infra)

The boilerplate's load-bearing core. Everything else codes against it.

- **Done:**
  - frozen `lib/contracts.py`; flat layout; `pyproject.toml`; docs; `CLAUDE.md`/`CHANGELOG.md`/`ROADMAP.md`.
  - `lib/registry.py` — `build(layer, name, **kwargs)` lazy-importlib factory; full REGISTRY map (llm/embedder/vectorstore/graphstore).
  - `config/settings.py` — `Settings.load(profile)` merges profile YAML + per-layer `CHASSIS_<LAYER>_IMPL` env overrides (the live-pivot path); `.build(layer)` ties settings → registry.
  - `config/profiles/` — `qdrant-local.yaml`, `chroma-inmem.yaml`, `faiss-bare.yaml`.
  - `lib/trace.py` — `TraceBus`: `deque(maxlen=500)` behind a lock + per-run JSONL sink; `emit()` / `recent(component_prefix=)`.
  - Offline tests for all three (13) + `[tool.pytest] pythonpath`; mypy + ruff clean.
  - `lib/llm/` — `AnthropicLLM` + `OpenAILLM` (lazy SDK, pure helpers) + `OllamaLLM` (stdlib urllib, zero deps). `LLM` contract.
  - `lib/embeddings/` — `SbertEmbedder` (minilm/bge) + `OpenAIEmbedder` (1536-dim fixed). `Embedder` contract.
  - `[project.optional-dependencies]` groups per adapter; mypy + ruff clean. Real round-trips deferred (need keys/models).
  - `lib/vectorstore/` — `MemoryStore` (zero-dep) + `FaissStore` + `ChromaStore` + `QdrantStore`. `VectorStore` contract.
  - `lib/embeddings/hashing.py` — `HashingEmbedder` (zero-dep, lexical). `lib/retriever.py` — `SimpleRetriever`.
  - `lib/ingestion/pipeline.py` — `load()` + `ingest()` (.md/.txt/.pdf, trace-emitting).
  - `scripts/smoke.py --stage ingest` + `config/profiles/memory.yaml`: **real e2e ingest passes offline, zero deps**. 35 tests total.
- **Needed:**
  - `docker-compose.yml` / `docker-compose.prod.yml` / `Dockerfile` / `Caddyfile` (recon §4; profile-aware).
  - `justfile` (recon §3; house recipe set).
  - `smoke.py --stage e2e` (needs orchestration); `tests/conftest.py` (SDK-boundary mocks).
- **Notes:** logger + no-silent-failures mandate is cross-cutting (recon §2), subordinate to the trace bus.

## Wave 1 — Domain layers (parallelizable, one owner each)

Each owns one `app/*` package and codes against the frozen contracts.

- **Orchestration** (`app/orchestration/`) — router (`retrieval`/`synthesis`/`chitchat`) + specialists + loop returning `Answer`, emitting trace. Chitchat answered directly by the orchestrator. Contract: `Orchestrator`.
- **Memory** (`app/memory/`) — short-term window + long-term vector recall + summarize-on-overflow. Contract: `Memory`.
- **Guardrails** (`app/guardrails/`) — input rails (length, named injection classes, PII), output rails (schema, grounded-in-context), LLM judge, manager that logs every check. Contract: `Guardrail` (recon §1; the marquee layer).
- **Eval** (`app/eval/`) — RAGAS-style faithfulness / answer-relevance / context-precision + judge + runner + `scripts/make_eval_set.py` (corpus-agnostic goldens). Contract: `Evaluator` (recon §6).

## Wave 2 — UI

- **`app/ui/`** — Gradio four-tab dashboard (Chat, Sources, Guardrails, Eval) reading the trace ring buffer on a timer.
- **Theming** — `app/ui/tokens.json` + `app/ui/theme.py` injecting CSS variables; METHODPROOF default (recon §9).
- **Data viz** — tables first; one embedded D3 router→specialist handoff swimlane as the centerpiece (recon §10). Resist building all four fancy.

## Options (off by default; build on a trigger)

- **Knowledge-graph retrieval** — contract done: `GraphNode`/`GraphEdge`/`GraphStore` added to `lib/contracts.py` and re-frozen. Remaining: a `GraphStore` adapter (default SQLite + NetworkX; Neo4j heavy option) + a `HybridRetriever` implementing `Retriever`, plus an `ingestion` step that emits nodes/edges and a `graphstore` registry slot + profile flag `retriever: vector|hybrid` (recon §8; stack-matrix Retrieval row).
- **RAGAS library** eval, **Guardrails AI / NeMo**, **LangGraph / CrewAI** orchestration, **Redis** memory — each a registry/profile swap with a named trigger (stack-matrix).
- **Figma workflow** — process, not code: `tokens.json` stays source of truth; use the figma skills to mirror tokens / push UI mockups (recon §11).

## Build method — Ralph army (deferred harness)

- `agents/*.yaml` + `skills/*/SKILL.md` + `ralph.py` adopting a shared-standards file, frontmatter+phases+gates specs, and a wave/gate supervisor with acceptance-command verification (recon §13). Per the v2 plan, run the army the night before so the repo ships integration-green; the live run is the flex with a guaranteed floor.

## Deliberately out of scope (YAGNI ledger)

Redis-persisted circuit breakers / persona scalers / numeric risk scores; multi-tenant graph scoping; 12-directory docs taxonomy; token build fan-out; Figma↔code auto-sync; an all-D3 dashboard; all eight themes ported; async anywhere. Each has a trigger recorded in the recon plan that would justify revisiting it.
