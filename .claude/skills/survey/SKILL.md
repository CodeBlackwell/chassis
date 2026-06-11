---
name: survey
description: "Stack-deliberation survey: walk a new assignment through the eleven deliberation layers as multiple-choice questions and record the decisions BEFORE any building. Use when: new assignment, new task, new problem received, start a feature, interview problem, pick the stack, deliberate the stack."
user_invocable: true
---

# Stack Survey

**This runs FIRST on any new assignment — before planning, PRD writing, or code.** It turns
the two reference docs into decisions: [deliberation-layers.md](../../../docs/reference/deliberation-layers.md)
says which layers this assignment contests; [stack-matrix.md](../../../docs/reference/stack-matrix.md)
supplies the options, pros/cons, and switch triggers for each. The output is a dated decision
record; nothing else happens until it exists.

---

## Step 0: Ingest

1. Take the assignment from the user's message/args. If none was given, ask for it (one
   sentence is enough).
2. Read `docs/reference/deliberation-layers.md` and `docs/reference/stack-matrix.md` in full.
   The survey's content comes from those files, not from memory — they evolve.

## Step 1: Classify

Map the assignment to the closest scenario family (or families) in the deliberation doc's
contested-layers table. That yields:

- **Contested layers** — the 2-4 layers the table names for that family. These get survey
  questions.
- **The two couplings** — vector DB and embedder are ALWAYS asked, regardless of family.
  They are the only irreversible decisions (deployment shape; dimension frozen at ingest).
- **Everything else** — auto-accepted on its matrix default. No question; recorded as
  "default, uncontested".

Also contest any layer where the assignment's wording plainly fires a switch trigger from the
matrix (e.g. "must run air-gapped" fires the local-only trigger even if the family doesn't
contest layer 3). Trigger text beats family table.

## Step 2: Survey (AskUserQuestion — never free text)

Ask via the **AskUserQuestion tool**, batched ≤4 questions per call, in this order:

1. **Framing check** (1 question): the scenario family you classified, as options, so a
   misread is caught before it shapes everything downstream.
2. **The two couplings** (vector DB, embedder).
3. **The contested layers**, one question per layer.

Rules for every question:

- **One undecided layer = one question.** Header = a short layer name (≤12 chars).
- **Options come from that layer's matrix table** — max 4: the default plus the 2-3
  alternatives whose switch trigger most plausibly matches this assignment. Omitted rows are
  reachable via the built-in "Other" — never pad with implausible options.
- **Each option's description must carry three parts**, compressed from the matrix row:
  `Pros: … Cons: … Choose when: …` — where "Choose when" is the situational breakdown,
  rewritten **in terms of this assignment**, not copied generically.
- **The recommended option goes first with "(Recommended)" in its label.** Recommend the
  default unless the assignment's wording fires another option's switch trigger — then
  recommend that option and say in its description which trigger fired.
- `multiSelect: false` — these are stack decisions, one winner per layer.

Do NOT ask about layers that are neither contested nor trigger-fired. The survey's value is
spending the user's attention only where the matrix says it matters.

## Step 3: Record

Write `docs/plans/YYYY-MM-DD_stack-survey-<slug>.md` (today's date, short assignment slug):

```markdown
# Stack survey — <assignment title>

**Assignment:** <one-paragraph restatement>
**Scenario family:** <family> (confirmed by user)

## Decisions

| Layer | Decision | Why (trigger or default) |
|-------|----------|--------------------------|
| Vector DB (coupling #1) | <choice> | <user's pick + the trigger that justified it> |
| Embedder (coupling #2) | <choice> | <…> |
| <contested layer> | <choice> | <…> |

## Accepted defaults (uncontested)

<one line per remaining layer: "Layer — default — no trigger fired">

## Profile sketch

```yaml
# config/profiles/<name>.yaml — implied by the decisions above
llm:         {impl: …}
embedder:    {impl: …}
vectorstore: {impl: …}
…
```

## Watch-list

<switch triggers from the chosen rows that could fire mid-build, so the team knows the
re-decision points in advance>
```

Offer to write the actual profile YAML if the sketch differs from an existing profile.

## Step 4: Proceed

Only after the record is saved: continue with the original task — implementation directly, or
hand off to `/prd` if this becomes a Ralph build (the PRD's Technical Considerations section
should cite the survey record). Every subsequent decision honors the record; if a watch-list
trigger fires mid-build, update the record, don't silently deviate.

---

## Pre-save checklist

- [ ] Both reference docs were read this session (not recalled from memory)
- [ ] Framing check asked before any layer question
- [ ] Both couplings asked, regardless of scenario family
- [ ] Every question used AskUserQuestion with Pros/Cons/Choose-when in each description
- [ ] Recommended option listed first, with the firing trigger named when it isn't the default
- [ ] Uncontested layers auto-defaulted, not asked
- [ ] Decision record saved under `docs/plans/` with date prefix before proceeding
