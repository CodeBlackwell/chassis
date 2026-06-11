---
name: recon
description: "Take a complex assignment, coordinate the research subagent suite (tech-researcher fan-out → matrix-author → default-skeptic), and produce a clear, indexed, sectioned options-and-considerations report. Use when: recon, research options for, evaluate choices for, what should we use for, options report, compare approaches for."
user_invocable: true
---

# Recon — Assignment → Options & Considerations Report

Coordinate the `.claude/agents/` suite to turn a complex assignment (e.g. "RAG over legal
contracts with on-prem constraints", "add agentic orchestration to X") into one user-friendly,
indexed report. The house precedent is `docs/plans/2026-06-09_workspace-recon-plan.md` — that
report shape produced a full build; this skill automates producing it.

All agents read `.claude/agents/_shared-standards.md`; so should you before starting.

---

## Phase 1 — Intake

Restate the assignment in one sentence. If any of these are missing, ask up to 3 clarifying
questions with lettered options (skip what the prompt already answers):

1. **Decision context** — what will this report be used to decide? (build plan / PRD input /
   pure survey)
2. **Hard constraints** — keys/budget, offline/on-prem, existing stack commitments, timeline
3. **Depth** — quick scan (3-4 topics, default skeptic-lite) or full recon (all relevant
   layers, full adversarial pass)

## Phase 2 — Decompose into topics

Break the assignment into 3-7 research topics. Where the assignment maps onto CHASSIS layers
(LLM, embeddings, vector DB, retrieval, orchestration, memory, guardrails, eval, UI,
deployment), use the layer as the topic boundary; add assignment-specific topics (domain data
shape, compliance, inference pipeline, …) as needed.

**Show the topic list with a one-line scope per topic and get a nod before fanning out** — the
fan-out is the expensive step and a wrong decomposition wastes all of it.

## Phase 3 — Research fan-out (parallel)

Launch one `tech-researcher` per topic **in a single parallel batch** (Agent tool,
`subagent_type: tech-researcher`). Each prompt must carry: the topic, the assignment's hard
constraints from Phase 1, and any couplings already known (so researchers flag conflicts).

Collect the Lesson/Sources/Adoption briefs. If a brief comes back thin (few sources, no
workspace prior art checked), re-launch that one topic with sharpened scope — don't accept a
weak leg silently.

## Phase 4 — Matrix + skeptic

1. `matrix-author`: pass all briefs; have it write the per-topic options matrices **into a
   working section of the report file** (Phase 5's path) — NOT into
   `docs/reference/stack-matrix.md` unless the assignment is explicitly about revising
   CHASSIS's own defaults.
2. `default-skeptic`: pass ONLY the matrices + brief summaries (clean-room — never the raw
   research). Collect per-topic verdicts (SURVIVES / FALLS), hardened triggers, and the
   rejection ledger.

## Phase 5 — Assemble the report

Write `docs/plans/YYYY-MM-DD_<assignment-slug>-recon.md` (today's date) with exactly this
skeleton — the indexing and sectioning are the deliverable, not decoration:

```markdown
# Recon: [Assignment]

**Date:** YYYY-MM-DD · **Status:** draft · **Decision it supports:** [from Phase 1]
**Constraints:** [hard constraints, one line]

## Index
[Linked TOC: every section + each topic, one line each with its bottom-line recommendation —
a reader who stops here knows the answer]

## 1. Executive summary
| Topic | Recommendation | Why (one line) | Confidence | Skeptic verdict |
[One row per topic. Then 3-5 sentences: the overall shape, the riskiest call, what to verify first.]

## 2. How to read this report
[3 lines: matrix format key, confidence tags, what "named trigger" means]

## 3..N. [One section per topic]
### Options
[The matrix: Option | Pros | Cons | Default? | Switch trigger]
### Considerations
[Prose, plain language: the trade-offs that actually drove the call, couplings with other
topics, what the skeptic attacked and what survived]
### Recommendation
[Bold one-liner + the trigger that would change it]

## Couplings & cross-cutting constraints
[The interactions BETWEEN topics — ordered by how early they lock you in]

## Rejected options (ledger)
[Every option/feature deliberately not recommended, each with the trigger that reopens it]

## Open questions & verification gaps
[What no source could answer; which claims are vendor-only; what a spike should test first]

## Appendix: sources
[Per topic, ranked by the evidence hierarchy, with dates]
```

Writing rules: lead every section with its conclusion; complete sentences, no jargon chains;
technical terms spelled out on first use; nothing in the report depends on having read the
agents' raw output.

## Phase 6 — Close

- Verbally give the user the executive summary + the report path.
- Offer the natural next steps: `/prd` (the report's recommendations seed the stories), or a
  spike on the top item in "Open questions".

## Degraded mode

If the subagents are unavailable (Agent tool can't resolve them), do the same phases inline and
sequentially, keeping the same report skeleton — and say so in the report's Status line
("inline, no adversarial pass"), because a report without the skeptic is a survey, not a recon.

## Quality bar (check before delivering)

- [ ] Index lets a reader find any decision in <10 seconds and carries the bottom line per topic
- [ ] Exactly one recommendation per topic; every alternative has a named trigger
- [ ] Skeptic verdict visible per topic (or Status admits there was no skeptic)
- [ ] Rejected-options ledger present (a recon that rejects nothing didn't look hard enough)
- [ ] Sources dated and ranked; vendor-only claims flagged
- [ ] Report stands alone — no reference to this conversation
