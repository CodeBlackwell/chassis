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

### Notes

- Contracts are **frozen**. The only planned change is a deliberate pre-build addition of a `GraphStore` Protocol + `HybridRetriever` for the knowledge-graph option (recon plan §8).
- Deferred to later passes: `lib/registry.py`, `lib/trace.py`, `config/settings.py`, all adapters, `lib/ingestion/`, every `app/*` layer, `scripts/`, the Ralph harness, `docker-compose`/`Dockerfile`/`justfile`, and `tests/`.
