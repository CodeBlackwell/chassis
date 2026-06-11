# Shared Standards — CHASSIS agent suite

Every agent in this directory reads this file first. It holds the house formats and rules;
it points at `CLAUDE.md` for the engineering mandates rather than restating them.

## The repo in one line

CHASSIS is a contracts-first base for multi-agent RAG projects: `lib/contracts.py` is **frozen**,
adapters implement it, the registry + profiles select the stack. Read `CLAUDE.md` (the hub) before
touching anything; the seven engineering mandates live there.

## Gates (the only definition of "working")

```bash
just lint && just test
uv run python scripts/smoke.py --stage e2e --corpus docs --profile memory   # full-loop smoke
```

## House research format (per topic)

Each researched topic is written up as three sections, mirroring
`docs/plans/2026-06-09_workspace-recon-plan.md`:

- **Lesson.** What the evidence shows, in 2-5 sentences. Claims carry a confidence tag
  (Certain / Likely / Unlikely) and a citation.
- **Sources.** Every source consulted, ranked by the evidence hierarchy below.
- **Adoption.** One of: **Default** / **Option** (with named switch trigger) / **Deferred**
  (with trigger) / **YAGNI** (with the trigger that would reopen it).

## House matrix format (per layer)

Tables in `docs/reference/stack-matrix.md` use exactly:

`| Option | Pros | Cons | Default? | Switch trigger |`

Rules: the default is the **lowest-friction option that still demonstrates the concept**;
exactly one default per table; every non-default row needs a **named trigger** — a specific
signal, never a vibe; cross-layer couplings get a `>` callout under the table.

## Evidence hierarchy

1. Workspace prior art (BLACKBOX repos — production code beats any document)
2. Official documentation (Context7 / vendor docs)
3. Independent benchmarks and postmortems
4. Blog posts and vendor marketing (lowest; flag when a claim rests only on these)

## Honesty rules

- Report failures plainly, with output. Never round "mostly works" up to "works".
- No claim without a citation or a verification you actually ran.
- Distinguish what you verified from what you read.

## Docs taxonomy

`docs/architecture/` system shape · `docs/guides/` how-to · `docs/reference/` lookup matrices ·
`docs/plans/` + `docs/features/` dated `YYYY-MM-DD_slug.md` records · `docs/runbooks/` ops.
