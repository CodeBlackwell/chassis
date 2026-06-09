# Workspace Recon → CHASSIS Injection Plan (2026-06-09)

Eight read-only recon sweeps across the BLACKBOX workspace (SPICE, PROVE, PANEL, veridatum, methodproof, code-review-graph, bloodtrail, crackpedia, flowhana, specter-1, kata, Payloads, THEMES) to extract battle-tested patterns and decide how each one enters CHASSIS's DNA.

## How to read this

Each domain lists: the **lesson**, the **canonical source** to copy from, and the **injection** — where it lands in CHASSIS and at what altitude:

- **Default** — ships in the boilerplate, on by default.
- **Option** — a swappable adapter or a profile flag; off unless a trigger fires.
- **Deferred** — named, with a home, built in a later pass.
- **YAGNI** — found, deliberately *not* adopted now; recorded so we don't rediscover it.

The minimalism filter is doing real work here. The recon surfaced a lot of production heavyweight machinery (Redis-persisted circuit breakers, persona threshold-scalers, 12-directory doc taxonomies, multi-tenant graph scoping). For a contracts-first interview boilerplate, most of that is weight. It's logged under YAGNI with a trigger that would justify it later.

## Frozen-contract impact (read first)

The contracts in `lib/contracts.py` are frozen. This plan honors that:

- **One proposed addition:** a `GraphStore` protocol + a `HybridRetriever` (knowledge-graph option, §8). This is a *new optional layer* added **pre-build** — allowed under extensibility Move 2, not a mid-build change. It does not alter any existing Protocol.
- **`Verdict` stays as-is.** SPICE argues for `risk_score` / `risk_level` / `adjusted_output`; for CHASSIS that detail rides in `Verdict.reasons` (and the trace payload). No contract change.
- Everything else **implements existing contracts** — no new surface.

---

## 1. Guardrails — the marquee layer

**Lesson.** SPICE's risk engine is a refuse-by-default pipeline of small, pure `(bool, reason_code)` checks run in a fixed order, returning a structured decision with *all* reasons (not the first). methodproof contributes field-proven PII regexes and a type-whitelist/required-field validation posture. veridatum contributes a schema-diff model (orphans / mismatches / within-tolerance) that maps cleanly onto an output rail. Payloads contributes **named** prompt-injection attack classes — the offensive-security flex: the input rail names what it blocks.

**Sources.**
- SPICE `services/execution-engine/src/execution_engine/risk/risk_validation.py` (ordered pipeline, composite reasons), `shared/src/trader_shared/risk_rules.py` (pure `(bool, reason)` checks).
- methodproof `app/export/anonymizer.py` (email/phone/api-key/env-var regexes), `app/ingestion/router.py` (frozenset type whitelist + required-metadata map).
- veridatum `src/veridatum/compare.py` + `tolerance.py` (structured comparison result).
- Payloads `payloads/CLAUDE.md` (8 named injection classes: system-prompt override, role injection, context escape, chained injection, encoding/obfuscation, hypothetical jailbreak, authority escalation, boundary escape).

**Injection — Default.** `app/guardrails/` (deferred build):
- `checks.py` — pure functions returning `(bool, reason_code)`, the SPICE shape.
- Input rails: `LengthRail`, `PromptInjectionRail` (the 8 named classes as labeled heuristics), `PiiRail` (methodproof regexes).
- Output rails: `SchemaRail` (veridatum-style), `GroundingRail` (answer grounded in `Answer.contexts`).
- `LLMJudgeRail` — Haiku safety judge returning a `Verdict`.
- `GuardrailManager` — runs rails in order, first BLOCK wins, **logs every check**.

**YAGNI (triggers in parens).** Circuit breakers + Redis-persisted guardrail state (prod multi-session durability). Persona/decision-mode threshold-scalers (a product with risk tiers). `risk_score` numeric compositing (when a single block/pass is too coarse). Async rails (the no-async rule holds at this scale).

## 2. Structured logging + no-silent-failures — cross-cutting DNA

**Lesson.** Every repo bans `print()`/`console.log()` and bans silent `except: pass`. PROVE's `StructuredLogger` adds request-scoped session windowing + cost tracking; methodproof's is a leaner contextvar version.

**Sources.** PROVE `src/core/logger.py`; methodproof `app/core/logger.py`.

**Injection — Default, but subordinate to the trace bus.** CHASSIS's primary observability is the `TraceEvent` bus (`lib/trace.py`, deferred) — that's what the UI reads. The StructuredLogger is the *ops* companion (JSONL + console). Adopt the leaner methodproof shape. The real DNA is the **mandate**, recorded in CHASSIS's `CLAUDE.md`: structured events only, every `except` logs, no silent failures.

## 3. Justfile — developer-ergonomics DNA

**Lesson.** A recurring recipe taxonomy with two reflexes: `set dotenv-load` at the top, and a `-`-prefixed port-kill before `dev` (ignore-failure). `default: @just --list` for discoverability. `deploy` = `git push → ssh → git pull → docker compose up -d --build`. Deploy host/dir come from `env()`, never hardcoded.

**Sources.** PROVE/veridatum/kata/crackpedia justfiles (canonical small form); methodproof root justfile (`prod-*` tunnel→migrate pattern); flowhana (bash-shebang recipes with trap cleanup).

**Injection — Default.** `justfile` (deferred build): `default` (list), `setup` (uv sync), `services` (compose up infra only), `dev` (port-kill + run), `test`, `lint` (ruff + mypy), `ingest` (corpus path arg), `eval`, `smoke`, `build`, `deploy`, `logs`, `clean`. Profile-aware where it matters.

## 4. Docker — the deployment coupling, made real

**Lesson.** Dev compose exposes services for debugging; prod compose hides DBs on an `internal: true` network behind a single Caddy entrypoint, with healthchecks + `depends_on: condition: service_healthy` + `restart: unless-stopped`. Dockerfile uses `uv sync --frozen --no-dev`, slim base, non-root user. This is exactly CHASSIS's "vector-DB drives deployment" coupling: Qdrant → compose; Chroma/FAISS → a single Dockerfile or bare process.

**Sources.** flowhana + PROVE `docker-compose.prod.yml` (internal net + Caddy); methodproof Dockerfile (uv, init-then-app); the `Caddyfile` reverse-proxy form already documented in workspace CLAUDE.md.

**Injection — Default (profile-aware).** `docker-compose.yml` (app + Qdrant, exposed) for the `qdrant-local` profile; `docker-compose.prod.yml` (internal net + Caddy); `Dockerfile` (uv, non-root); `Caddyfile`. For `chroma-inmem` / `faiss-bare` profiles, the compose collapses to the single Dockerfile — the coupling stated in `docs/architecture.md` becomes literal files.

## 5. Config + registry — the flexibility engine

**Lesson.** PROVE's `Settings.load()` (dataclass + `load_dotenv` + `os.getenv` defaults) paired with a `build_clients(settings)` factory that switches concrete classes on a provider string. This *is* CHASSIS's registry+profiles mechanism, already proven.

**Sources.** PROVE `src/config/settings.py`, `src/core/client_factory.py`.

**Injection — Default.** `config/settings.py` + `lib/registry.py` (deferred): `Settings.load(profile)` resolves the profile YAML, then per-layer env vars override (`CHASSIS_LLM_IMPL`, …). `registry.build(layer, name, **kwargs)` is the factory. This is the live-pivot path the failure playbook depends on.

## 6. Eval harness

**Lesson.** PROVE's eval is a `golden.json` of cases + substring/keyword scoring + per-case cost/latency from the logger session, printed as a table with optional JSON. Hand-written goldens catch regressions; start at ~5–10 cases.

**Sources.** PROVE `eval/run.py` (golden + score_case + cost); code-review-graph `evaluate/`.

**Injection — Default custom; RAGAS = Option.** `app/eval/` (deferred): RAGAS-style faithfulness / answer-relevance / context-precision + an LLM judge + a runner producing a table/CSV; `scripts/make_eval_set.py` generates goldens from the live corpus (corpus-agnostic, "the system writes its own exam"). Swap to the RAGAS library only if the room wants named metrics and time allows.

## 7. Testing + smoke + CI

**Lesson.** Mock at the SDK boundary (PROVE patches `anthropic.Anthropic`); `setup_method`/`teardown_method` with temp stores (code-review-graph); a single e2e smoke that ingests → queries → answers → evals one row. CI = parallel lint/type/test jobs, Python matrix, coverage gate; deploy gated behind tests.

**Sources.** PROVE `tests/test_claude_chat_client.py`; code-review-graph `tests/` + `.github/workflows/ci.yml`; specter-1 `.github/workflows/ci.yml` (test-gates-deploy).

**Injection — Default.** `tests/conftest.py` (SDK-boundary mocks, temp dirs) + `scripts/smoke.py` (`--stage ingest|e2e`) + `.github/workflows/ci.yml` (ruff + mypy + pytest + smoke). Tests assert against *contracts*, so they survive any adapter swap.

## 8. Knowledge-graph retrieval — new Option (the one contract addition)

**Lesson.** Vector and graph RAG coexist. PROVE does vector-hit → graph-expand for connected evidence (Neo4j, vectors-inside). code-review-graph proves the light path: SQLite nodes/edges + NetworkX for traversal + optional embeddings, graceful-degrade to keyword. methodproof shows scoped Cypher; bloodtrail shows shortest-path.

**Sources.** code-review-graph `code_review_graph/graph.py` + `embeddings.py` (the light default to copy); PROVE `src/core/neo4j_client.py` + `src/qa/tools.py` `get_connected_evidence` (the hybrid-expand pattern); bloodtrail (reachability).

**Injection — Option (pre-build contract addition).** Add a `GraphStore` Protocol and a `HybridRetriever` (implements the existing `Retriever`) behind a profile flag `retriever: vector|hybrid`. Default graph backend = **SQLite + NetworkX in-process** (light, no service, matches the "zero-service" deployment story); **Neo4j = heavy option** (trigger: >100k chunks or real multi-hop). Becomes a new row in `docs/stack-matrix.md` and a realized example of extensibility Move 2.

**YAGNI.** Multi-tenant ViewScope graph scoping (methodproof) — only if CHASSIS is re-skinned into a multi-tenant product.

## 9. Design DNA / theming — new Option

**Lesson.** A single `tokens.json` is the source of truth; a build step fans it into per-consumer CSS; a `[data-theme]` attribute toggles light/dark. The workspace has 8 production themes (METHODPROOF/SHOMEN+KINMYAKU, ĀNUENUE, SHINKAI, PROVE, SCHEMANCER, CRACKPEDIA, KATA, BLOODTRAIL). METHODPROOF's 5-color node palette maps naturally onto trace event types (AI→gold, test→green, moment→red, human→ink).

**Sources.** `THEMES/METHODPROOF.md` (+ SHINKAI/others); methodproof `methodproof-tokens/tokens.json` + `build.mjs`; the `[data-theme]` toggle in `methodproof-dashboard`.

**Injection — Option, default theme = METHODPROOF.** `app/ui/tokens.json` + `app/ui/theme.py` (load tokens → inject CSS custom properties into Gradio via `Blocks(css=...)`). One `THEME` flag selects the palette. This is what makes the demo look intentional instead of default-Gradio-grey. Keep it to **one default theme + the swap mechanism**; do not port all 8.

## 10. Data visualization — the four UI tabs

**Lesson.** Reuse consistent encodings: a green→…→purple scale for AI-ratio, stable glyph/shape registries, hover-tooltip-as-portal, incremental render from a streamed event buffer. Gradio's table is fine for logs but weak for time-axis interaction; a small embedded D3 in `gr.HTML` (~34KB) buys a real swimlane.

**Sources.** methodproof-dashboard SwimLaneGraph/ThreadView + `docs/features/2026-04-12_graph-rubric.md`; PROVE `src/static/graph.js` (treemap/bars, SSE-accumulate); bloodtrail force graph; kata schema cards.

**Injection — Default plain Gradio + ONE embedded D3 centerpiece (YAGNI on the rest).** All four tabs read the trace ring buffer on a `gr.Timer` tick. Chat tab embeds a **single** D3 router→specialist handoff swimlane (the centerpiece slide). Sources/Guardrails/Eval ship as Gradio tables/dataframes first; promote to D3 only if time allows. Reuse the METHODPROOF color tokens from §9 so encodings are consistent.

## 11. Figma workflow — Option / process, low priority

**Lesson.** The workspace's Figma pipeline is deliberately manual: design in Figma, hand-copy hex into `tokens.json`, rebuild. Skills exist for both directions (`figma-generate-library` to scaffold a token library from code; `figma-generate-design` to push a UI layout into Figma; `figma-code-connect` for two-way component mapping).

**Sources.** methodproof `docs/architecture/2026-04-09_brand-asset-manifest.md`; the `figma-*` skills; `THEMES/*.md` Figma source links.

**Injection — Option, documented not coded.** A short process note: keep `app/ui/tokens.json` the source of truth; use `figma-generate-library` once to mirror tokens into a CHASSIS Figma file as reference; use `figma-generate-design` to push the Gradio four-tab concept into Figma for design critique. No automation/sync — overkill for a single Gradio consumer.

## 12. Documentation discipline — DNA (adopt light)

**Lesson.** methodproof's gold standard: a dated-doc convention (`YYYY-MM-DD_slug-verb.md`), a `docs/INDEX.md` hub, `CHANGELOG.md` + `ROADMAP.md`, and a `CLAUDE.md` that *points at* docs ("reference — don't inline") rather than hoarding knowledge.

**Sources.** methodproof `docs/INDEX.md`, `docs/NAMING_CONVENTION.md`, `CHANGELOG.md`, `ROADMAP.md`, `CLAUDE.md`.

**Injection — Default, light.** Adopt the **dated-doc convention** (this file follows it) and add `CHANGELOG.md`, `ROADMAP.md`, and a CHASSIS `CLAUDE.md` hub. Keep `docs/` **flat** for now — the 12-subdirectory taxonomy is YAGNI until the doc count justifies it (trigger: docs/ exceeds ~15 files).

## 13. Agent / skill orchestration — build-method DNA

**Lesson.** SPICE's 28 agents share one `_shared-standards.md` instead of duplicating rules; agents and skills are Markdown with frontmatter + sequenced phases + explicit gates before destructive actions; a supervisor reacts to events via runbooks; work fans out in parallel waves and gates between them. This is exactly the Ralph army's shape.

**Sources.** SPICE `.claude/agents/_shared-standards.md`, `.claude/agents/*.md`, `.claude/skills/sp-operate/SKILL.md`, `services/orchestrator/.../supervisor/daemon.py`.

**Injection — Deferred (Ralph harness).** `agents/*.yaml` + `skills/*/SKILL.md` + `ralph.py` adopt: a shared-standards file, frontmatter+phases+gates spec shape, and the wave/gate supervisor with acceptance-command verification (already the plan's false-completion guard). The four authored skills (`rag-agent-scaffold`, `eval-harness`, `architecture-diagram`, `slides`) follow the SKILL.md shape.

---

## Decision summary

| Domain | Altitude | Lands in | Default backend / note |
|--------|----------|----------|------------------------|
| Guardrails (rails + judge + manager) | Default | `app/guardrails/` | named injection classes, methodproof PII, veridatum schema |
| Structured logging + no-silent-failures | Default (mandate) | `lib/` logger + `CLAUDE.md` | subordinate to the trace bus |
| Justfile | Default | `justfile` | dotenv-load, port-kill, env-driven deploy |
| Docker | Default (profile-aware) | `docker-compose*.yml`, `Dockerfile`, `Caddyfile` | Qdrant→compose; Chroma/FAISS→Dockerfile |
| Config + registry | Default | `config/settings.py`, `lib/registry.py` | profile → env override |
| Eval harness | Default (custom) | `app/eval/`, `scripts/make_eval_set.py` | RAGAS lib = option |
| Tests + smoke + CI | Default | `tests/`, `scripts/smoke.py`, `.github/workflows/` | SDK-boundary mocks |
| Knowledge-graph retrieval | **Option (1 contract add)** | `GraphStore` + `HybridRetriever` | SQLite+NetworkX default; Neo4j heavy |
| Design DNA / theming | Option | `app/ui/tokens.json`, `app/ui/theme.py` | METHODPROOF default theme |
| Data viz | Default + 1 D3 | `app/ui/` tabs | tables + one D3 handoff swimlane |
| Figma | Option (process) | a process doc | manual, no sync |
| Docs discipline | Default (light) | `CHANGELOG`, `ROADMAP`, `CLAUDE.md`, dated docs | flat docs/ for now |
| Agent/skill orchestration | Deferred | `agents/`, `skills/`, `ralph.py` | shared-standards + wave/gate |

## Deliberately NOT adopting now (YAGNI ledger)

- Redis-persisted circuit breakers / guardrail state, persona scalers, numeric risk scores (SPICE) — prod durability, not interview.
- Multi-tenant graph ViewScope scoping (methodproof) — only if re-skinned multi-tenant.
- 12-directory docs taxonomy, token build-fan-out to 5 consumers, Figma↔code auto-sync — premature for one app.
- All-D3 dashboard, all 8 themes ported — one centerpiece viz + one theme is enough to read as intentional.
- Async anywhere — the no-async rule from the v2 plan holds.

## Next actions (proposed, not yet executed)

1. Thread the two new **stack-matrix rows** (knowledge-graph retriever; theming) into `docs/stack-matrix.md`.
2. When Wave 0 builds: realize §2–7 (logger, justfile, docker, config+registry) as the foundation.
3. Make the §8 `GraphStore` addition to `lib/contracts.py` a deliberate, reviewed pre-build edit (the only contract change), then freeze again.
4. Author `CLAUDE.md`, `CHANGELOG.md`, `ROADMAP.md` for CHASSIS (§12).
