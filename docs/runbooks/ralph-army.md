# Runbook — Ralph's Army (the build harness)

How to run autonomous builds against this repo. The runner is `scripts/ralph.py` (vendored from
[the Army-of-Ralph gist](https://gist.github.com/CodeBlackwell/5c2c2ee797f4de874564e0393a1e7f88));
PRD bundles live under `prds/<feature-slug>/`. Requires the `claude` CLI on PATH.

## The two modes

| Mode | Command | When |
|------|---------|------|
| **Solo** | `just ralph prds/<slug> [iters]` | <20 stories, single-domain. One agent, one task per iteration: find first `[ ]` in `PRD.md`, implement, test, mark `[x]`, commit, repeat. |
| **Army** | `just army prds/<slug>` | 20+ stories, multi-domain. Parallel agents per wave, gates between waves, verified completion. |

## Authoring a PRD bundle

Invoke the `/prd` skill (it asks mode + scope, then writes the bundle), or copy
`prds/_example/` and fill it in by hand. An army bundle is self-contained:

```
prds/<slug>/
├── PRD.md                      # roster + Orchestrator Config (WAVE_N_AGENTS / WAVE_N_GATE)
├── agents/<name>-agent.md      # one spec per agent: mission, owned paths, stories
├── progress/progress-<name>.txt # one tracker per agent: checkboxes + completion signal
└── logs/                       # created by ralph.py (gitignored)
```

Rules that keep parallel agents from colliding:

- **Every path has exactly one writer.** Same-wave agents never touch the same file; shared
  paths are read-only. `lib/contracts.py` is frozen — no agent owns it.
- **Max 4 stories per agent** (one context window each). Split bigger domains.
- **Gates between waves** — for CHASSIS, `just lint && just test`; add the e2e smoke
  (`uv run python scripts/smoke.py --stage e2e --corpus docs --profile memory` — any non-empty
  corpus folder works) on the final wave. A failed gate re-launches the wave's agents with the
  error appended (3 tries).

## Three-layer completion (the false-"done" guard)

1. Agent finishes → writes the **delivered** tag (`<delivered>…`) to its progress file.
2. Ralph pre-checks: any `[ ]` left → auto-reject.
3. A separate **verification Claude** reads the progress file, checks owned files exist, runs
   the gates; only it writes the **verified** tag (`<verified>…`). Rejection strips the
   delivered tag and re-launches the agent.

**Never put a literal completion tag in a template or spec** — Ralph substring-matches
progress files, so a tag in instruction text false-positives the agent as done.

## Recovery

Progress files are the checkpoint. If an agent crashes or exhausts context, re-run the same
command — completed stories stay `[x]`, agents resume from the first `[ ]`, verified agents
are skipped. Timing lands in `prds/<slug>/ralph_timing.log`; per-agent stdout in
`prds/<slug>/logs/`.

## Pre- and post-run suite (`.claude/agents/`)

The army is bracketed by a decision/verification loop of subagents (all read
`_shared-standards.md` first). The **`/recon` skill is the front door to the pre-run half**:
give it a complex assignment and it runs intake → topic decomposition → the pipeline below →
an indexed options-and-considerations report at `docs/plans/<date>_<slug>-recon.md`, which
then seeds `/prd`.

```
tech-researcher ×N ─► matrix-author ─► default-skeptic ─► /prd ─► ARMY ─► delivery-auditor ─► readout-writer
   (parallel,          (stack-matrix     (attack the                        (promises vs        (dated readout +
    one topic each)     format)           defaults)                          shipped + gates)    CHANGELOG/ROADMAP)
```

- **Pre:** fan out one `tech-researcher` per topic (vector DB, orchestration, inference, UI…);
  `matrix-author` compresses the briefs into `docs/reference/` tables; `default-skeptic` attacks
  each proposed default and hardens the switch triggers. The hardened matrix feeds `/prd`.
- **Post:** `delivery-auditor` verifies the *integrated whole* against the PRD (Ralph only
  verifies per-agent); its gap list seeds the next PRD. `readout-writer` (provisional) files the
  dated `docs/features/` readout and syncs CHANGELOG/ROADMAP — closing the loop.

## House practice

Run the army the night before a deadline so the repo ships integration-green; a live run is
the flex with a guaranteed floor (recon plan §13).
