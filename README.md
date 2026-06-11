# CHASSIS

A flexible, contracts-first base repo for sophisticated multi-agent projects. Not a single app — a base you re-skin per project. Every layer (LLM provider, embeddings, vector DB, orchestration, memory, guardrails, evaluation, UI, deployment) sits behind a contract and is selected by config, not hard-wired.

The flexibility mechanism in one sentence: `lib/contracts.py` defines what each layer must do, the `lib/*/` adapters implement it three ways, a registry picks one from config, and named profiles switch a whole backend with a single flag.

## Layout

Flat, multi-package layout — `lib/`, `app/`, and `config/` are top-level importable packages (there is no `src/` and no top-level `chassis` package). This is dictated by the frozen import paths in the contracts (`lib.contracts`, `lib.llm.openai_llm`, `app.orchestration`).

```
lib/     shared infra — contracts, registry, trace bus, adapters, ingestion
app/     domain layers — orchestration, memory, guardrails, eval, ui
config/  env-driven settings + named stack profiles
docs/    categorical subdirs — architecture/, guides/, reference/, plans/, features/, runbooks/
```

## Docs

- [docs/architecture/architecture.md](docs/architecture/architecture.md) — the system at rest, the trace bus, query flow, the two couplings.
- [docs/guides/extensibility.md](docs/guides/extensibility.md) — how to add an adapter or a layer, add a profile, and re-skin CHASSIS into a new project.
- [docs/reference/stack-matrix.md](docs/reference/stack-matrix.md) — per-layer pro/cons matrix with defaults and switch triggers.

## Status: skeleton

This is the minimal first pass: the directory tree, the **frozen contracts** (`lib/contracts.py`), and the docs. Deferred to later passes: `registry.py`, `trace.py`, `config/settings.py`, all adapters, ingestion, every `app/*` layer, the build harness, `docker-compose`, `justfile`, and tests. Empty dirs are placeholders with a documented destiny in the docs.
