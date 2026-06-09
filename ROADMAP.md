# Roadmap

Build order for CHASSIS, by wave and layer. No dates — the workspace builds fast. Each section lists **Done**, **Needed**, and **Notes**. Source of truth for *what* each layer must satisfy is `lib/contracts.py`; source for *which option is default* is [docs/stack-matrix.md](docs/stack-matrix.md); source for *which workspace pattern to copy* is the [recon plan](docs/2026-06-09_workspace-recon-injection-plan.md).

## Wave 0 — Foundation (the pre-bakeable infra)

The boilerplate's load-bearing core. Everything else codes against it.

- **Done:** frozen `lib/contracts.py`; flat layout; `pyproject.toml`; docs; `CLAUDE.md`/`CHANGELOG.md`/`ROADMAP.md`.
- **Needed:**
  - `config/settings.py` — `Settings.load(profile)` resolving a profile YAML then per-layer env overrides (recon §5; copy PROVE `settings.py`).
  - `lib/registry.py` — `build(layer, name, **kwargs)` factory (recon §5; copy PROVE `client_factory.py`).
  - `config/profiles/` — `qdrant-local.yaml`, `chroma-inmem.yaml`, `faiss-bare.yaml`.
  - `lib/trace.py` — `TraceEvent` bus: `deque(maxlen=500)` behind a lock + JSONL sink (architecture doc).
  - `lib/llm/` — anthropic + openai + ollama adapters (`LLM` contract).
  - `lib/embeddings/` — sbert (minilm/bge) + openai (`Embedder`). Lock dim before ingest.
  - `lib/vectorstore/` — qdrant + chroma + faiss (`VectorStore`).
  - `lib/ingestion/` — corpus-agnostic load → chunk → embed → upsert (.md/.txt/.pdf).
  - `docker-compose.yml` / `docker-compose.prod.yml` / `Dockerfile` / `Caddyfile` (recon §4; profile-aware).
  - `justfile` (recon §3; house recipe set).
  - `scripts/smoke.py` (`--stage ingest|e2e`), `tests/conftest.py` (SDK-boundary mocks).
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

- **Knowledge-graph retrieval** — add `GraphStore` Protocol + `HybridRetriever` (the one pre-build contract addition, then re-freeze). Default backend SQLite + NetworkX; Neo4j heavy option (recon §8; stack-matrix Retrieval row).
- **RAGAS library** eval, **Guardrails AI / NeMo**, **LangGraph / CrewAI** orchestration, **Redis** memory — each a registry/profile swap with a named trigger (stack-matrix).
- **Figma workflow** — process, not code: `tokens.json` stays source of truth; use the figma skills to mirror tokens / push UI mockups (recon §11).

## Build method — Ralph army (deferred harness)

- `agents/*.yaml` + `skills/*/SKILL.md` + `ralph.py` adopting a shared-standards file, frontmatter+phases+gates specs, and a wave/gate supervisor with acceptance-command verification (recon §13). Per the v2 plan, run the army the night before so the repo ships integration-green; the live run is the flex with a guaranteed floor.

## Deliberately out of scope (YAGNI ledger)

Redis-persisted circuit breakers / persona scalers / numeric risk scores; multi-tenant graph scoping; 12-directory docs taxonomy; token build fan-out; Figma↔code auto-sync; an all-D3 dashboard; all eight themes ported; async anywhere. Each has a trigger recorded in the recon plan that would justify revisiting it.
