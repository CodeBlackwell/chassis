# Roadmap

Build order for CHASSIS, by wave and layer. No dates — the workspace builds fast. Each section lists **Done**, **Needed**, and **Notes**. Source of truth for *what* each layer must satisfy is `lib/contracts.py`; source for *which option is default* is [docs/reference/stack-matrix.md](docs/reference/stack-matrix.md); source for *which workspace pattern to copy* is the [recon plan](docs/plans/2026-06-09_workspace-recon-plan.md).

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
  - `Dockerfile` (uv, non-root, `EXTRAS` arg) + `.dockerignore` + `docker-compose.yml` (Qdrant+app) + `docker-compose.prod.yml` (internal net + Caddy) + `Caddyfile`; both compose files validate.
  - `justfile` (house recipes); `just --list` + `just ingest` run. App-server CMD (`app.ui`) activates with Wave 2.
- **Needed:**
  - `smoke.py --stage e2e` (needs orchestration); `tests/conftest.py` (SDK-boundary mocks).
- **Notes:** logger + no-silent-failures mandate is cross-cutting (recon §2), subordinate to the trace bus.

## Wave 1 — Domain layers (parallelizable, one owner each)

Each owns one `app/*` package and codes against the frozen contracts.

- **Orchestration** (`app/orchestration/`) — DONE. `router` + `specialists` (LLM or extractive) + `DefaultOrchestrator` (input rail → route → memory → specialist → output rail → `Answer`, emits trace). `smoke --stage e2e` runs offline. 6 tests. Contract: `Orchestrator`.
- **Memory** (`app/memory/`) — DONE. `BufferMemory` — deque window + long-term vector recall (evicted turns stay findable) + summarize-on-overflow (LLM optional). 6 offline tests. Contract: `Memory`.
- **Guardrails** (`app/guardrails/`) — STUB BY DESIGN. `PassthroughGuardrail` satisfies the `Guardrail` contract and is wired through the orchestrator's block seam, but enforces nothing — what counts as injection/PII/ungrounded is domain-specific, so the base ships the seam, not a policy. A project registers its own rail under `guardrail` and selects it in a profile; the orchestrator already honors a blocking verdict, so a real rail drops in with no other change. Contract: `Guardrail` (recon §1). 2 offline tests + an orchestration test that the block seam fires.
- **Eval** (`app/eval/`) — DONE. `metrics` (faithfulness/answer-relevance/context-precision) + `RagasEvaluator` (+ optional judge, summary, CSV) + `runner` + `dataset`/`make_eval_set.py` (corpus-agnostic goldens). 8 tests. Contract: `Evaluator` (recon §6).

**Wave 1 complete.** All four domain layers built, tested offline, contract-conformant.

## Wave 2 — UI (DONE)

- **`app/ui/`** — Gradio four-tab dashboard (Chat, Sources, Guardrails, Eval); `build_app` injects the orchestrator + trace bus + eval_fn; `python -m app.ui` launches on :8000. Construction tested + launch verified (HTTP 200).
- **Theming** — `tokens.json` + `theme.py` inject CSS variables; METHODPROOF SHOMEN/KINMYAKU default. `CHASSIS_THEME=dark` flips it.
- **Data viz** — tables/markdown shipped (the YAGNI line held). No further viz planned: anything flow-shaped would couple the UI to one orchestrator's topology, against the contract boundary (recon §10 swimlane struck 2026-06-10).

## Options (off by default; build on a trigger)

- **Knowledge-graph retrieval** — contract done: `GraphNode`/`GraphEdge`/`GraphStore` added to `lib/contracts.py` and re-frozen. Remaining: a `GraphStore` adapter (default SQLite + NetworkX; Neo4j heavy option) + a `HybridRetriever` implementing `Retriever`, plus an `ingestion` step that emits nodes/edges and a `graphstore` registry slot + profile flag `retriever: vector|hybrid` (recon §8; stack-matrix Retrieval row).
- **RAGAS library** eval, **Guardrails AI / NeMo**, **LangGraph / CrewAI** orchestration, **Redis** memory — each a registry/profile swap with a named trigger (stack-matrix).
- **Figma workflow** — process, not code: `tokens.json` stays source of truth; use the figma skills to mirror tokens / push UI mockups (recon §11).

## Build method — Ralph army (INSTALLED)

- `scripts/ralph.py` (vendored from the Army-of-Ralph gist) — solo mode (one task per iteration) and army mode (parallel agents per wave, `WAVE_N` gate commands with retry, three-layer delivered/verified completion as the false-"done" guard — recon §13's acceptance-command verification). `just ralph <bundle>` / `just army <bundle>`.
- PRD bundles are self-contained at `prds/<slug>/` (`PRD.md` + `agents/` + `progress/`); `prds/_example/` is the template; the `/prd` skill (`.claude/skills/prd/SKILL.md`) generates bundles with CHASSIS gates (`just lint && just test`). Runbook: [docs/runbooks/ralph-army.md](docs/runbooks/ralph-army.md).
- Per the v2 plan, run the army the night before so the repo ships integration-green; the live run is the flex with a guaranteed floor.
- **Pre/post suite** (`.claude/agents/`, all referencing `_shared-standards.md`): `tech-researcher` (one topic per invocation, parallel fan-out) → `matrix-author` (house pro/con matrix) → `default-skeptic` (adversarial pass on defaults) feed `/prd`; `delivery-auditor` (integrated-whole verification, gap list → next PRD) and `readout-writer` (provisional — dated readout + doc sync) close the loop after a run. The `/recon` skill (`.claude/skills/recon/`) is the front door: assignment in → indexed options report in `docs/plans/` out. Lifecycle guards: `prd-skeptic` (pre-launch bundle review), `contract-guard` (mandate enforcement on diffs), `gate-verifier` (gate runs + minimal-repro triage; Ralph-style completion checks), `adapter-builder` (the scoped one-adapter wave template). Deferred with triggers: `trace-analyst` (first real trace-debug session), `reskin-scaffolder` (first actual re-skin). First live test: `/recon` the GraphStore backends ahead of the knowledge-graph PRD.

## Deliberately out of scope (YAGNI ledger)

Redis-persisted circuit breakers / persona scalers / numeric risk scores; multi-tenant graph scoping; 12-directory docs taxonomy; token build fan-out; Figma↔code auto-sync; an all-D3 dashboard; all eight themes ported; async anywhere. Each has a trigger recorded in the recon plan that would justify revisiting it.
