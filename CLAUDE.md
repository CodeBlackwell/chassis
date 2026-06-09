# CLAUDE.md — CHASSIS

Guidance for Claude Code working in this repo. This file is a **hub**: it points at `docs/` rather than inlining knowledge. Read the linked doc before working in a layer.

## What CHASSIS is

A contracts-first base repo for sophisticated multi-agent RAG projects. Not a single app — a base you re-skin per project. Every layer (LLM, embeddings, vector DB, retrieval, orchestration, memory, guardrails, eval, UI, deployment) sits behind a contract and is selected by config, not hard-wired.

The flexibility mechanism in one sentence: `lib/contracts.py` defines what each layer must do, the `lib/*/` adapters implement it, a registry picks one from config, and named profiles switch a whole backend with a single flag.

## Status: skeleton

Present: the directory tree, the **frozen contracts** (`lib/contracts.py`), and `docs/`. Deferred (named, with homes): `lib/registry.py`, `lib/trace.py`, `config/settings.py`, all adapters, `lib/ingestion/`, every `app/*` layer, `scripts/`, the Ralph harness, `docker-compose`/`Dockerfile`/`justfile`, and `tests/`. See [ROADMAP.md](ROADMAP.md) for the build order and [CHANGELOG.md](CHANGELOG.md) for what has shipped.

## Layout

Flat, multi-package layout — `lib/`, `app/`, `config/` are top-level importable packages (no `src/`, no top-level `chassis` package). This is dictated by the frozen import paths in the contracts (`lib.contracts`, `lib.llm.openai_llm`, `app.orchestration`).

```
lib/     shared infra — contracts, registry, trace bus, adapters, ingestion
app/     domain layers — orchestration, memory, guardrails, eval, ui
config/  env-driven settings + named stack profiles
docs/    architecture, extensibility, stack matrix, dated reference docs
```

## Commands

Tooling mirrors the workspace house style (uv + hatchling). A `justfile` is deferred; until then:

```bash
uv sync                              # install (dev group: ruff, mypy, pytest)
python -c "import lib.contracts"     # contracts import clean
uvx mypy lib                         # typecheck (must stay clean)
```

The deferred `justfile` will carry the house recipe set: `default` (list), `setup`, `services`, `dev` (port-kill + run), `test`, `lint`, `ingest <folder>`, `eval`, `smoke`, `build`, `deploy`, `logs`, `clean`. See the recon plan §3.

## Architecture

Read [docs/architecture.md](docs/architecture.md) — repo map, the flexibility mechanism, the trace bus, life-of-a-question flow, and the contract-type reference. Do not inline that content here.

### The two couplings (the only cross-layer constraints)

1. **Vector DB drives deployment.** Qdrant needs a service (compose); Chroma/FAISS run in-process (Dockerfile or bare). Decide the vector DB first.
2. **Embedder dim is frozen at ingest.** MiniLM ↔ bge is free (both 384-dim); OpenAI (1536) after ingest means re-ingest. Lock the embedder before ingesting.

## Frozen contracts — the prime directive

`lib/contracts.py` is frozen. Adapters and app layers code against it and never propose changes mid-build. If a contract seems wrong, log the complaint and work around it — contract churn is how parallel builds die. The one sanctioned pre-build addition (a `GraphStore` Protocol + `GraphNode`/`GraphEdge` for the knowledge-graph option, recon plan §8) was made 2026-06-09; contracts are **re-frozen** as of that change. No further edits in flight.

To extend without touching contracts, see [docs/extensibility.md](docs/extensibility.md): add an adapter (implement the Protocol → one registry line → reference in a profile), add a profile, or re-skin into a new project.

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
| [docs/architecture.md](docs/architecture.md) | system at rest, trace bus, query flow, couplings |
| [docs/extensibility.md](docs/extensibility.md) | add an adapter/layer/profile; re-skin into a new project |
| [docs/stack-matrix.md](docs/stack-matrix.md) | per-layer pro/cons matrix, defaults, switch triggers |
| [docs/2026-06-09_workspace-recon-injection-plan.md](docs/2026-06-09_workspace-recon-injection-plan.md) | workspace recon → which patterns enter CHASSIS (default/option/deferred/YAGNI) |
| [ROADMAP.md](ROADMAP.md) | build order per layer/wave |
| [CHANGELOG.md](CHANGELOG.md) | what has shipped |

## Documentation discipline

Dated reference docs follow `YYYY-MM-DD_slug.md`. Keep `docs/` flat until it justifies a taxonomy (trigger: ~15+ files). This `CLAUDE.md` is a navigation hub, not a knowledge sink — point at docs, do not inline.
