# CLAUDE.md — CHASSIS

Guidance for Claude Code working in this repo. This file is a **hub**: it points at `docs/` rather than inlining knowledge. Read the linked doc before working in a layer.

## What CHASSIS is

A contracts-first base repo for sophisticated multi-agent RAG projects. Not a single app — a base you re-skin per project. Every layer, from the model provider down to how answers are rendered and deployed, sits behind a contract and is selected by config, not hard-wired.

The flexibility mechanism in one sentence: `lib/contracts.py` defines what each layer must do, the `lib/*/` adapters implement it, a registry picks one from config, and named profiles switch a whole backend with a single flag.

## Status

Built and verified offline (66 tests, mypy + ruff clean): frozen contracts; the Wave 0 core (`registry`, `settings` + profiles, `trace` bus); all adapters (LLM trio, sbert/openai/hashing embedders, qdrant/chroma/faiss/memory stores); `ingestion` + `SimpleRetriever`; the full ingest + e2e smoke gates; docker/justfile; the Wave 1 layers `memory`, `orchestration`, `eval` (each a working default) plus `guardrails` as an intentional unopinionated stub (`PassthroughGuardrail` — the seam is wired, the policy is left to each project); the Wave 2 Gradio dashboard (`app/ui`, `python -m app.ui`); and the Ralph army build harness (`scripts/ralph.py` + `prds/` bundles + the `/prd` skill — see [docs/runbooks/ralph-army.md](docs/runbooks/ralph-army.md)). Still deferred: the knowledge-graph adapter (`GraphStore`/`HybridRetriever` — contract in place). See [ROADMAP.md](ROADMAP.md) and [CHANGELOG.md](CHANGELOG.md).

The whole system runs with **zero keys/services/deps** via the `memory` profile; swap to the real stack by changing one profile flag.

## Layout

Flat, multi-package layout — `lib/`, `app/`, `config/` are top-level importable packages (no `src/`, no top-level `chassis` package). This is dictated by the frozen import paths in the contracts (`lib.contracts`, `lib.llm.openai_llm`, `app.orchestration`).

```
lib/     shared infra — contracts, registry, trace bus, adapters, ingestion
app/     domain layers — orchestration, memory, guardrails, eval, ui
config/  env-driven settings + named stack profiles
docs/    categorical subdirs — architecture/, guides/, reference/, plans/, features/, runbooks/
prds/    Ralph build-harness bundles (PRD + agents/ + progress/ per feature); _example/ is the template
```

## Commands

Tooling mirrors the workspace house style (uv + hatchling). The `justfile` carries the recipe set (`just --list`):

```bash
just setup                           # uv sync (dev group: ruff, mypy, pytest)
just test                            # pytest
just lint                            # ruff + mypy (must stay clean)
just ingest <folder>                 # ingest a corpus (default: memory profile)
just dev                             # launch the dashboard on :8000 (--extra ui)
just ralph prds/<slug>               # Ralph solo build loop (just army … for gated waves)
uv run python scripts/smoke.py --stage e2e --corpus <folder> --profile memory
```

Adapter deps are `[project.optional-dependencies]` groups — `uv sync` installs the light base; add `--extra ui` / `--extra embeddings-sbert` etc. for a real stack.

## Architecture

Read [docs/architecture/architecture.md](docs/architecture/architecture.md) — repo map, the flexibility mechanism, the trace bus, life-of-a-question flow, and the contract-type reference. Do not inline that content here.

### The two couplings (the only cross-layer constraints)

1. **Vector DB drives deployment.** Qdrant needs a service (compose); Chroma/FAISS run in-process (Dockerfile or bare). Decide the vector DB first.
2. **Embedder dim is frozen at ingest.** MiniLM ↔ bge is free (both 384-dim); OpenAI (1536) after ingest means re-ingest. Lock the embedder before ingesting.

## Frozen contracts — the prime directive

`lib/contracts.py` is frozen. Adapters and app layers code against it and never propose changes mid-build. If a contract seems wrong, log the complaint and work around it — contract churn is how parallel builds die. The one sanctioned pre-build addition (a `GraphStore` Protocol + `GraphNode`/`GraphEdge` for the knowledge-graph option, recon plan §8) was made 2026-06-09; contracts are **re-frozen** as of that change. No further edits in flight.

To extend without touching contracts, see [docs/guides/extensibility.md](docs/guides/extensibility.md): add an adapter (implement the Protocol → one registry line → reference in a profile), add a profile, or re-skin into a new project.

## Engineering standards (mandates)

1. **Structured events only** — no `print()`. The `TraceEvent` bus is primary observability; a thin StructuredLogger is the ops companion.
2. **No silent failures** — every `except` logs. No bare `except: pass`.
3. **Sync everywhere** — no async at this scale; it buys nothing and costs debugging time.
4. **Type annotations** — `mypy lib app` stays clean.
5. **Dataclasses, not Pydantic, in contracts** — Pydantic is allowed inside guardrails for schema validation but never leaks into `lib/contracts.py`.
6. **Path ownership** — a layer edits only its own package plus its one-line registry entry.
7. **YAGNI** — default to the lowest-friction option that demonstrates the concept; switch only on a named trigger.

## Key docs

| Doc | Contents |
|-----|----------|
| [docs/architecture/architecture.md](docs/architecture/architecture.md) | system at rest, trace bus, query flow, couplings |
| [docs/guides/extensibility.md](docs/guides/extensibility.md) | add an adapter/layer/profile; re-skin into a new project |
| [docs/reference/stack-matrix.md](docs/reference/stack-matrix.md) | per-layer pro/cons matrix, defaults, switch triggers |
| [docs/plans/2026-06-09_workspace-recon-plan.md](docs/plans/2026-06-09_workspace-recon-plan.md) | workspace recon → which patterns enter CHASSIS (default/option/deferred/YAGNI) |
| [ROADMAP.md](ROADMAP.md) | build order per layer/wave |
| [CHANGELOG.md](CHANGELOG.md) | what has shipped |

## Documentation discipline

`docs/` is categorical: `architecture/` (system shape), `guides/` (how-to), `reference/` (lookup matrices), `plans/` (dated planning/decision records), `features/` (dated feature docs), `runbooks/` (ops). Dated docs follow `YYYY-MM-DD_slug.md` and live in `plans/` or `features/`. This `CLAUDE.md` is a navigation hub, not a knowledge sink — point at docs, do not inline.
