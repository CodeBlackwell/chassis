# Product Requirements Document (PRD) Template

Copy this bundle (`prds/_example/` → `prds/<feature-slug>/`) to start a feature. The `/prd`
skill (`.claude/skills/prd/SKILL.md`) generates all of this from a feature description.

## Overview

**Project Name:** [Your Project Name]
**Version:** 1.0
**Last Updated:** [Date]

## Executive Summary

[2-3 sentences describing what the project does and who it's for]

---

## Orchestrator Config

Ralph's Army (`scripts/ralph.py --army`) reads wave assignments and gate commands from this block.

```
WAVE_0_AGENTS=("foundation")
WAVE_0_GATE="just lint && just test"

WAVE_1_AGENTS=("feature-a" "feature-b")
WAVE_1_GATE="just lint && just test"

WAVE_2_AGENTS=("polish")
WAVE_2_GATE="just lint && just test && uv run python scripts/smoke.py --stage e2e --corpus docs --profile memory"
```

### Agent Roster

| Agent | Wave | Stories | Owned Paths |
|-------|------|---------|-------------|
| foundation | 0 | US-001 to US-004 | `lib/<new-adapter>/`, registry entry |
| feature-a | 1 | US-010 to US-013 | `app/<layer-a>/`, `tests/test_<layer-a>.py` |
| feature-b | 1 | US-020 to US-023 | `app/<layer-b>/`, `tests/test_<layer-b>.py` |
| polish | 2 | US-080 to US-082 | `app/ui/` (refinements only) |

---

## Feature Domains

### Domain 1: Foundation (Wave 0)
**Owner:** foundation-agent

| ID | Story | Priority |
|----|-------|----------|
| US-001 | [Shared infra story — adapters, profiles, registry] | P0 |
| US-002 | [Story] | P0 |

### Domain 2: [Feature A] (Wave 1)
**Owner:** feature-a-agent

| ID | Story | Priority |
|----|-------|----------|
| US-010 | [Story] | P0 |
| US-011 | [Story] | P0 |

### Domain 3: [Feature B] (Wave 1)
**Owner:** feature-b-agent

| ID | Story | Priority |
|----|-------|----------|
| US-020 | [Story] | P0 |
| US-021 | [Story] | P1 |

---

## Ownership Map

| Path | Owner | Access |
|------|-------|--------|
| `lib/<new-adapter>/` | foundation | WRITE |
| `app/<layer-a>/` | feature-a | WRITE |
| `app/<layer-b>/` | feature-b | WRITE |
| `lib/contracts.py` | nobody | READ-ONLY (frozen) |
| `lib/registry.py` | one line per agent's own entry | coordinate |

---

## Wave Dependencies

```
Wave 0: Foundation
   │
   ├──► Wave 1: Core Features (parallel)
   │       ├── feature-a-agent
   │       └── feature-b-agent
   │
   └──► Wave 2: Polish (after Wave 1)
           └── polish-agent
```
