# CLAUDE.md — CHASSIS

Guidance for Claude Code working in this repo. This file is a **hub**: it points at `docs/` rather than inlining knowledge. Read the linked doc before working in a layer.

## What CHASSIS is

A contracts-first base repo for sophisticated multi-agent RAG projects. Not a single app — a base you re-skin per project. Every layer, from the model provider down to how answers are rendered and deployed, sits behind a contract and is selected by config, not hard-wired.

The flexibility mechanism in one sentence: `lib/contracts.py` defines what each layer must do, the `lib/*/` adapters implement it, a registry picks one from config, and named profiles switch a whole backend with a single flag.

**Deletable by design.** A direct consequence of the concept: any real project built on CHASSIS will contain code it should delete. The base ships several options per seam, so when a project picks option C, the adapters for options A and B are dead weight — deliberately cheap dead weight, since each is one file plus one registry line. Deleting the unchosen options is an expected re-skin step, not a smell.

## Status

Built and verified offline (79 tests, mypy + ruff clean): frozen contracts; the Wave 0 core (`registry`, `settings` + profiles, `trace` bus); all adapters (LLM trio, sbert/openai/hashing embedders, qdrant/chroma/faiss/memory stores); tool-calling on the LLM contract (`ToolSpec`/`ToolCall`, provider-native mappings in all three LLM adapters, and the generic `run_tool_loop` in `app/orchestration/tools.py` — the loop ships, the tools are per-project); `SimpleRetriever`; docker/justfile; the Wave 1 layers `memory`, `orchestration`, `eval` (each a working default) plus `guardrails` as an intentional unopinionated stub (`PassthroughGuardrail` — the seam is wired, the policy is left to each project); the Wave 2 Gradio dashboard (`app/ui`, `python -m app.ui`); the JSON API (`app/api`, `python -m app.api` — `POST /ask` + `GET /trace` over the same orchestrator seam, no auth/CORS by design); and the Ralph army build harness (`scripts/ralph.py` + `prds/` bundles + the `/prd` skill — see [docs/runbooks/ralph-army.md](docs/runbooks/ralph-army.md)). Still deferred: the knowledge-graph adapter (`GraphStore`/`HybridRetriever` — contract in place). Deliberately not shipped: an ingestion pipeline — loading/chunking is per-project; the seam is `Chunk` → `Embedder` → `VectorStore.upsert`, and the stack matrix's Ingestion section carries the options. See [ROADMAP.md](ROADMAP.md) and [CHANGELOG.md](CHANGELOG.md).

The whole system runs with **zero keys/services/deps** via the `memory` profile; swap to the real stack by changing one profile flag.

## Survey first — in all circumstances

On receiving any new assignment, task, or feature request — **before planning, PRD writing, or
code** — run the `/survey` skill (`.claude/skills/survey/SKILL.md`). It walks the assignment
through the deliberation layers as a multiple-choice survey (options, pros/cons, and a
situational breakdown per undecided layer, sourced from the two reference docs) and saves a
dated decision record under `docs/plans/` before anything proceeds. The two couplings are
always asked; uncontested layers auto-default. Subsequent work honors the record.

## Layout

Flat, multi-package layout — `lib/`, `app/`, `config/` are top-level importable packages (no `src/`, no top-level `chassis` package). This is dictated by the frozen import paths in the contracts (`lib.contracts`, `lib.llm.openai_llm`, `app.orchestration`).

```
lib/     shared infra — contracts, registry, trace bus, adapters
app/     domain layers — orchestration, memory, guardrails, eval, ui
config/  env-driven settings + named stack profiles + defaults.py (centralized tuning knobs)
docs/    categorical subdirs — architecture/, guides/, reference/, plans/, features/, runbooks/
prds/    Ralph build-harness bundles (PRD + agents/ + progress/ per feature); _example/ is the template
```

## Commands

Tooling mirrors the workspace house style (uv + hatchling). The `justfile` carries the recipe set (`just --list`):

```bash
just setup                           # uv sync (dev group: ruff, mypy, pytest)
just test                            # pytest
just lint                            # ruff + mypy (must stay clean)
just dev                             # launch the dashboard on :8000 (--extra ui)
just api                             # launch the JSON API on :8001 (--extra api)
just ralph prds/<slug>               # Ralph solo build loop (just army … for gated waves)
```

Adapter deps are `[project.optional-dependencies]` groups — `uv sync` installs the light base; add `--extra ui` / `--extra embeddings-sbert` etc. for a real stack.

## Architecture

Read [docs/architecture/architecture.md](docs/architecture/architecture.md) — repo map, the flexibility mechanism, the trace bus, life-of-a-question flow, and the contract-type reference. Do not inline that content here.

### The two couplings (the only cross-layer constraints)

1. **Vector DB drives deployment.** Qdrant needs a service (compose); Chroma/FAISS run in-process (Dockerfile or bare). Decide the vector DB first.
2. **Embedder dim is frozen at ingest.** MiniLM ↔ bge is free (both 384-dim); OpenAI (1536) after ingest means re-ingest. Lock the embedder before ingesting.

## Frozen contracts — the prime directive

`lib/contracts.py` is frozen. Adapters and app layers code against it and never propose changes mid-build. If a contract seems wrong, log the complaint and work around it — contract churn is how parallel builds die. Three sanctioned between-build additions have been made: the knowledge-graph option (`GraphStore` Protocol + `GraphNode`/`GraphEdge`, recon plan §8, 2026-06-09), tool-calling (`ToolSpec`/`ToolCall`, additive defaulted fields on `Message`/`LLMResponse`, `tools=` kwarg on `LLM.chat`), and `VectorStore.delete` for corpus freshness (both 2026-06-11). Contracts are **re-frozen** as of these. No further edits in flight.

To extend without touching contracts, see [docs/guides/extensibility.md](docs/guides/extensibility.md): add an adapter (implement the Protocol → one registry line → reference in a profile), add a profile, or re-skin into a new project.

## Engineering standards (mandates)

1. **Structured events only** — no `print()`. The `TraceEvent` bus is primary observability; a thin StructuredLogger is the ops companion.
2. **No silent failures** — every `except` logs. No bare `except: pass`.
3. **Sync everywhere** — no async at this scale; it buys nothing and costs debugging time.
4. **Type annotations** — `mypy lib app` stays clean.
5. **Dataclasses, not Pydantic, in contracts** — Pydantic is allowed inside guardrails for schema validation but never leaks into `lib/contracts.py`.
6. **Path ownership** — a layer edits only its own package plus its one-line registry entry.
7. **YAGNI** — default to the lowest-friction option that demonstrates the concept; switch only on a named trigger.
8. **Tuning knobs live in `config/defaults.py`** — no scattered magic ints/strings; each knob's inline comment cites the consuming module(s) (paths, not line numbers). Adding or moving a usage means updating the citation.

## Key docs

| Doc | Contents |
|-----|----------|
| [docs/architecture/architecture.md](docs/architecture/architecture.md) | system at rest, trace bus, query flow, couplings |
| [docs/guides/extensibility.md](docs/guides/extensibility.md) | add an adapter/layer/profile; re-skin into a new project |
| [docs/reference/stack-matrix.md](docs/reference/stack-matrix.md) | per-layer pro/cons matrix, defaults, switch triggers |
| [docs/reference/deliberation-layers.md](docs/reference/deliberation-layers.md) | which layers need deliberating per scenario; contested-layers map |
| [docs/plans/2026-06-09_workspace-recon-plan.md](docs/plans/2026-06-09_workspace-recon-plan.md) | workspace recon → which patterns enter CHASSIS (default/option/deferred/YAGNI) |
| [ROADMAP.md](ROADMAP.md) | build order per layer/wave |
| [CHANGELOG.md](CHANGELOG.md) | what has shipped |

## Documentation discipline

`docs/` is categorical: `architecture/` (system shape), `guides/` (how-to), `reference/` (lookup matrices), `plans/` (dated planning/decision records), `features/` (dated feature docs), `runbooks/` (ops). Dated docs follow `YYYY-MM-DD_slug.md` and live in `plans/` or `features/`. This `CLAUDE.md` is a navigation hub, not a knowledge sink — point at docs, do not inline.
