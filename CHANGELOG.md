# Changelog

All notable changes to CHASSIS. Format follows [Keep a Changelog](https://keepachangelog.com/); this project is pre-1.0 and not yet versioned.

## [Unreleased]

### Added

- **Tool-calling on the LLM contract (sanctioned between-build extension, 2026-06-11).**
  `ToolSpec` + `ToolCall` dataclasses; `Message` gains a `tool` role, `tool_calls`, and
  `tool_call_id`; `LLMResponse` gains `tool_calls`; `LLM.chat` gains a `tools=` kwarg.
  All additive with defaults — existing adapters and callers untouched. All three LLM
  adapters map to their provider's native tool API (Anthropic `tool_use`/`tool_result`
  blocks, OpenAI function tool-calls, Ollama function format with synthesized call ids)
  via pure offline-tested helpers. `app/orchestration/tools.py` ships `run_tool_loop` —
  the generic call → execute → feed-back loop (round budget in
  `config/defaults.py:TOOL_LOOP_MAX_ITERS`, unknown tool names fed back to the model and
  traced, never raised). Per the philosophy, CHASSIS ships the loop and the seam, not the
  tools. 10 new tests; 72 total.
- **JSON API layer (`app/api`).** `create_app(orchestrator, bus)` — a thin FastAPI app over
  the same `handle(query) -> Answer` seam the UI and eval consume: `POST /ask` (the `Answer`
  dataclass as JSON), `GET /trace` (the trace-bus ring, filterable by component prefix),
  `GET /health`. Handlers are sync (FastAPI threadpool — the no-async mandate holds); no
  auth/rate-limiting/CORS by design — per-project policy on a wired seam. `python -m app.api`
  assembles the stack from the active profile exactly like the dashboard; `just api` serves
  on :8001 (`config/defaults.py:API_HOST/API_PORT`); `api` optional-dependency group
  (fastapi + uvicorn). 5 new tests; 77 total.
- **`VectorStore.delete(collection, ids)` (sanctioned between-build extension, 2026-06-11).**
  The corpus-freshness hole: with stable chunk ids, `upsert` already overwrites changed chunks,
  but chunks whose source document disappeared were unremovable. All four stores implement it —
  memory (filter), FAISS (`remove_ids` by position, parallel chunk list kept aligned), Chroma
  (native `delete`), Qdrant (uuid5 point-id mapping mirrored from upsert). The re-run/diff
  pattern is documented in the stack matrix's Ingestion section ("freshness is a re-run, not a
  pipeline"); scheduling stays per-project. 2 new tests; 79 total.
- **Deliberation-layers reference (`docs/reference/deliberation-layers.md`).** The question
  before the stack matrix: which of the ten decision layers (topology, control-flow authority,
  model tiers, tool surface, knowledge/retrieval, state/memory, data contracts, guardrails,
  budget/termination, observability/eval) a given problem actually contests. Each layer carries
  its option spectrum, its decider, and the CHASSIS default seam; a scenario-family table maps
  problem shapes to their contested layers. Designed to accrete rows/sections as new scenario
  families come up.
- **Researched option matrices for all ten deliberation layers** (ten parallel tech-researcher
  briefs, 2025–2026 landscape + workspace production evidence, compressed into the house
  matrix format in `docs/reference/stack-matrix.md`). Extended sections: Orchestration (new
  Topology and Control-flow-authority tables + framework note), LLM provider (Model tier
  strategy), Retrieval (upgrades table: rerankers, BM25+RRF, contextual/agentic retrieval,
  text-to-SQL), Memory (persistence, extraction-memory, graph/temporal, durable-execution rows
  + shared-state callout), Guardrails (moderation endpoints, classifier rails, judge-family
  rule, per-tool-policy callout), LLM eval (promptfoo row, judge-bias and CI notes). New
  sections: Budget & termination, Tool surface, Data contracts & structured output, Tracing &
  observability. Every CHASSIS default survived the research pass; the additions are named
  switch triggers, not new defaults.
- **`/survey` skill — the mandatory first step on any assignment.**
  `.claude/skills/survey/SKILL.md`: classifies a new assignment against the deliberation
  layers' scenario table, then surveys the user via multiple-choice questions
  (AskUserQuestion) covering only the contested layers plus the two irreversible couplings —
  each option carrying Pros/Cons/Choose-when compressed from the stack matrix, with the
  recommended option first and the firing trigger named when it isn't the default. Saves a
  dated decision record (decisions, accepted defaults, profile sketch, watch-list of mid-build
  triggers) to `docs/plans/` before any planning or code. Mandated in CLAUDE.md ("Survey first
  — in all circumstances") and introduced in the README ("Step zero").
- **Deliberation layer 11 — inference pipeline design.** How one query becomes one answer: the
  stage decomposition inside a route, distinct from topology (which shapes the agent graph).
  New section in `deliberation-layers.md` + a matrix in `stack-matrix.md`: single-prompt
  synthesis (default, the shipped specialists), staged SoC pipeline (gather → transform →
  curate → format, the PROVE QA pattern — out-of-band state, purpose-tagged calls, fallback
  chains, code-assembled structure), plan-then-write, map-reduce over sources, best-of-N +
  selection, and reflection — each with the failure mode that triggers it. Scenario table
  gained an "evidence-backed answers" family and layer 11 on cross-document synthesis.

- **Repo skeleton + frozen contracts.** Flat `lib/`/`app/`/`config/` layout; `lib/contracts.py` with all shared dataclasses (`Message`, `LLMResponse`, `Chunk`, `SearchResult`, `Turn`, `MemoryContext`, `Verdict`, `EvalRow`, `Answer`, `TraceEvent`) and Protocols (`LLM`, `Embedder`, `VectorStore`, `Retriever`, `Orchestrator`, `Memory`, `Guardrail`, `Evaluator`). Imports clean, `mypy` clean.
- **Hygiene.** `pyproject.toml` (hatchling, ruff line-length 100, mypy, zero runtime deps), `.gitignore`, MIT `LICENSE`, `README.md`, `.env.example`.
- **Core docs.** `docs/architecture.md` (flexibility mechanism, trace bus, query flow, the two couplings), `docs/extensibility.md` (add adapter/layer/profile, re-skin guide), `docs/stack-matrix.md` (per-layer pro/cons matrix).
- **Workspace recon.** `docs/plans/2026-06-09_workspace-recon-plan.md` — eight read-only sweeps across the BLACKBOX workspace mapping battle-tested patterns to CHASSIS seams (default/option/deferred/YAGNI).
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
  - `app/guardrails/checks.py`: pure `(passed, reason)` checks — length cap, **named** input-screening classes, PII regexes (email/phone/api-key), and lexical grounding.
  - `app/guardrails/guard.py`: `DefaultGuardrail` (satisfies `Guardrail`) — refuse-by-default input rail, non-empty + grounded output rail, plus an optional LLM safety judge. Deterministic without an LLM, so it tests fully offline.
  - 9 tests (each screening class blocked, benign passes, PII/length blocks, grounding, judge safe/unsafe via a fake LLM); 44 total. mypy + ruff clean.
- **Wave 1 — Memory layer.**
  - `app/memory/buffer.py`: `BufferMemory` (satisfies `Memory`) — a deque window (short-term) plus long-term vector recall (every turn embedded into its own collection, so evicted turns stay findable) plus summarize-on-overflow (running transcript without an LLM, condensed via LLM when supplied).
  - 6 tests (window eviction, recall of a turn-1 fact at turn 20, empty-query skip, overflow summary with/without LLM); 50 total. mypy + ruff clean.
- **Wave 1 — Orchestration + the first real e2e smoke.**
  - `app/orchestration/`: `router` (heuristic retrieval/synthesis/chitchat), `specialists` (LLM-synthesized or extractive fallback), `DefaultOrchestrator` (satisfies `Orchestrator`) — `handle(query) -> Answer` running input rail → route → memory context → specialist → output rail, emitting a `TraceEvent` at each step. Consumes `Retriever`/`Memory`/`Guardrail`; LLM optional.
  - `scripts/smoke.py --stage e2e`: ingest + orchestrated answer through the configured stack; the `memory` profile runs it with **zero keys/services/deps** (extractive answers). Trace shows the full `guardrail→route→memory→retrieval→guardrail→answer` flow.
  - 6 tests (router ≥9/10, grounded answer with citations, injection blocked, chitchat, ≥3 trace events, memory records both turns); 56 total. mypy + ruff clean.
- **Wave 1 — Eval layer (completes Wave 1).**
  - `app/eval/metrics.py`: RAGAS-style lexical metrics — faithfulness, answer-relevance, context-precision (each `[0,1]`).
  - `app/eval/evaluator.py`: `RagasEvaluator` (satisfies `Evaluator`) — fills row scores, optional LLM-as-judge; `summary()` + `to_csv()`.
  - `app/eval/runner.py`: `answer_rows()` (run questions through the orchestrator) + `report()`.
  - `app/eval/dataset.py` + `scripts/make_eval_set.py`: corpus-agnostic seed-set generation (LLM writes the exam; degenerate fallback offline).
  - 8 tests + a real offline eval run (generate → answer → score); 64 total. mypy + ruff clean.
- **Wave 2 — Gradio dashboard + theme.**
  - `app/ui/`: `theme.py` + `tokens.json` (METHODPROOF SHOMEN/KINMYAKU, CSS-variable injection), `format.py` (pure trace/sources/guardrail/eval table helpers), `app.py` (`build_app` — four tabs Chat/Sources/Guardrails/Eval, Gradio lazy-imported, layers injected), `__main__.py` (`python -m app.ui` wires the configured stack and launches on :8000).
  - `gradio` added as the `ui` optional dep; the Dockerfile default `EXTRAS` and `just dev` now build/serve it.
  - 7 tests (tokens, CSS light/dark, table formatters, real `build_app` construction); launch verified (HTTP 200). 71 total. mypy + ruff clean.
- **De-opinionation pass (flexibility audit).**
  - Registry now covers the app layers too: `retriever`/`memory`/`guardrail`/`orchestrator`/`evaluator` slots; `Settings.build(layer, **extra)` accepts constructed dependencies; all five added to `_OVERRIDABLE`. `app/ui/__main__.py` and `scripts/smoke.py` build the whole stack from the profile — no more hard-wired `Default*` imports. Profiles gain `impl` keys per layer (the dead `memory: {window, recall_k}` knobs now actually flow; `retrieval: {k}` moved into the `orchestrator` section).
  - Eval tab columns derive from `EvalRow.scores` keys (`format.eval_table`) instead of hardcoding RagasEvaluator's three metric names, so a swapped Evaluator renders correctly.
  - Guardrail policy is config, not code: `DefaultGuardrail(block_pii=, min_overlap=)` exposed and profile-driven; `checks.py` documents its English/NANP-locale pattern lists as defaults.
  - 74 tests; mypy + ruff clean; both smoke stages pass on the `memory` profile.

- **Ralph army build harness (closes the deferred ROADMAP item).**
  - `scripts/ralph.py` — vendored from the [Army-of-Ralph gist](https://gist.github.com/CodeBlackwell/5c2c2ee797f4de874564e0393a1e7f88), ruff-cleaned: solo mode (one PRD task per iteration, commit-on-green) + army mode (parallel `claude -p` agents per wave, `WAVE_N_GATE` commands with 3-retry re-launch on failure, three-layer delivered→verified completion so agents can't claim "done" falsely).
  - PRD bundles are self-contained at `prds/<slug>/` (`PRD.md` + `agents/` + `progress/`, `logs/` gitignored); `prds/_example/` carries the templates adapted to CHASSIS gates (`just lint && just test`, e2e smoke on the final wave, `lib/contracts.py` owned by nobody).
  - `/prd` generator skill at `.claude/skills/prd/SKILL.md` (story sizing, ownership maps, wave plans → a runnable bundle); runbook at `docs/runbooks/ralph-army.md` (first resident of `runbooks/`); `just ralph` / `just army` recipes; `tqdm` joins the dev group.
  - The empty top-level `agents/`/`skills/`/`progress/` placeholders are superseded by the per-bundle layout and removed.
- **Pre/post-Ralph agent suite.** Five subagents under `.claude/agents/` plus the `_shared-standards.md` keystone (house research format, matrix format, evidence hierarchy, gates — SPICE's shared-standards pattern). Pre-run: `tech-researcher` (read-only; one topic per invocation, Lesson/Sources/Adoption briefs, workspace-prior-art-first evidence hierarchy) → `matrix-author` (compresses briefs into the `docs/reference/` pro/con matrix format) → `default-skeptic` (clean-room adversarial pass: scale/cost/migration/lock-in/honesty attacks on each default, hardens switch triggers, emits the rejection ledger). Post-run: `delivery-auditor` (integrated-whole audit Ralph's per-agent verification can't see — promises vs `git diff` evidence, gates, registry/profile seam checks, gap list as next-PRD stories) and `readout-writer` (provisional: dated `docs/features/` readout + CHANGELOG/ROADMAP sync). Domain topics (RAG, ReAct, vector DBs, inference, React/UI) are invocation parameters, not per-domain agents — the agents encode method, the matrix holds the knowledge.
- **Lifecycle-guard agents (completes the suite).** Four more under `.claude/agents/`: `prd-skeptic` (read-only adversarial review of a PRD bundle before the army launches — leaked completion tags, ownership overlaps, >4-story agents, wave-order bugs, unverifiable criteria; LAUNCH / FIX-FIRST verdict), `contract-guard` (read-only diff reviewer enforcing the seven engineering mandates as grep-able predicates plus semantic review; refuses to fix, by design), `gate-verifier` (runs lint/test/smoke, absorbs the noisy logs, returns verdict + minimal repro; doubles as a Ralph-style completion verifier on a progress file), `adapter-builder` (one contract + one backend per invocation, writable paths hard-limited to the adapter module / one registry line / one profile key / one test file / one optional-dep group; offline tests mandatory). Deferred with named triggers: `trace-analyst`, `reskin-scaffolder`.
- **`/recon` skill (the suite's front door).** `.claude/skills/recon/SKILL.md`: complex assignment in → clarify constraints → decompose into 3-7 topics (user nod before the expensive fan-out) → parallel `tech-researcher` batch → `matrix-author` → clean-room `default-skeptic` → one indexed, sectioned options-and-considerations report at `docs/plans/YYYY-MM-DD_<slug>-recon.md` (linked TOC carrying per-topic bottom lines, executive-summary table with skeptic verdicts, per-topic Options/Considerations/Recommendation, couplings section, rejected-options ledger, dated+ranked sources, quality-bar checklist). Degraded inline mode if subagents are unavailable, flagged in the report status because no skeptic = survey, not recon.

- **Centralized tuning knobs (`config/defaults.py`).** The foundational ints + strings that shape app behavior — retrieval `k`, memory window/recall/collection, LLM temperature + token budgets, extractive-fallback snippet sizes, eval thresholds and seed-set size, trace ring size + runs dir, UI host/port, hashing dim — extracted from scattered default args into one import-free module every layer reads. Profiles still override the constructor-shaped ones per stack; `defaults.py` is the single place to finetune the rest.

### Removed

- **The smoke gate.** `scripts/smoke.py` and the `just smoke` / `just ingest` recipes are gone; the gates are `just lint && just test`. The loop the smoke exercised is covered by the offline test suite.
- **The ingestion pipeline (owner's call — references over pre-built pipelines).** `lib/ingestion/`, the `ingestion` extra (pypdf), `scripts/make_eval_set.py`, and the per-profile `ingestion:` block are gone. Loading and chunking are domain decisions, and a pre-built loader is the first thing a real project rips out — the base now ships the seam (`Chunk` → `Embedder.embed` → `VectorStore.upsert`) and a stack-matrix Ingestion section with the options and best practices instead. `app/eval/dataset.generate()` takes chunks instead of a corpus path; `python -m app.ui` no longer auto-ingests (projects wire their own `eval_fn` into `build_app`). Net: 62 tests.

### Changed

- **docs/ taxonomy.** Moved from flat to categorical subdirs ahead of the ~15-file trigger (owner's call): `architecture/`, `guides/`, `reference/`, `plans/` (dated planning records), plus empty-ahead-of-time `features/` and `runbooks/`. All links in `CLAUDE.md`/`README.md`/`ROADMAP.md`, in-doc cross-references, and code-comment paths updated; historical CHANGELOG entries keep their original paths.
- **Guardrails demoted to an unopinionated stub (owner's call — keep the base policy-free).** Replaced `DefaultGuardrail` + the pure `checks.py` (length / input-screening / PII / grounding heuristics) with `PassthroughGuardrail`: satisfies the `Guardrail` contract, always passes. The orchestrator's block seam is untouched, so a project drops in its own rail via the registry + a profile flag with no other change. Registry key `guardrail.default` → `guardrail.passthrough`; all four profiles updated. Tests cut from the screening-class suite to two passthrough checks plus an orchestration test that a blocking guardrail still short-circuits the seam. Net: 66 tests. The base now ships no built-in screening content, keeping it domain-neutral.

### Notes

- Contracts are **re-frozen** as of the `GraphStore` addition (2026-06-09). No further changes in flight; future extension happens via adapters, not contract edits.
- Deferred to later passes: `lib/registry.py`, `lib/trace.py`, `config/settings.py`, all adapters, `lib/ingestion/`, every `app/*` layer, `scripts/`, the Ralph harness, `docker-compose`/`Dockerfile`/`justfile`, and `tests/`.
