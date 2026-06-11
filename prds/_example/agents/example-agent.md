# Example Agent Specification

## Identity
- **Name**: example-agent
- **Wave**: 1 (runs in parallel with other Wave 1 agents)
- **Stories**: US-010 to US-013 (4 stories — max per agent)

## Mission
[Describe what this agent is responsible for. Be specific about the domain/feature area.]

Example: "Implement the `app/memory/` layer against the frozen `Memory` contract, including
window eviction, vector recall, and overflow summarization."

## Owned Paths (WRITE access)
These are the ONLY files/directories this agent can modify:

- `app/example/` - This agent's layer
- `tests/test_example.py` - Its tests
- `lib/registry.py` - ONLY its own one-line registry entry

## Shared Paths (READ-ONLY)
Files this agent can read but NOT modify (owned by other agents or frozen):

- `lib/contracts.py` - FROZEN. Code against it; never edit it
- `lib/trace.py` - Trace bus (owned by core)
- `config/` - Settings + profiles (coordinate for new profile keys)

## DO NOT MODIFY
Explicit list of files to never touch:

- `lib/contracts.py` (frozen — log a complaint and work around it)
- `pyproject.toml` (coordinate with foundation-agent for new deps)
- Other agents' `app/*` packages

## Dependencies
What must be complete before this agent can start:

- Wave 0 (foundation-agent) must be complete
- The contracts this layer codes against exist in `lib/contracts.py`

## Progress File
`progress/progress-example.txt`

---

## Stories

### US-010: [Title]
**Description:** As a [user], I want [feature] so that [benefit].

**Acceptance Criteria:**
- [ ] Specific verifiable criterion
- [ ] Another criterion
- [ ] `just lint && just test` passes

---

### US-011: [Title]
**Description:** ...

**Acceptance Criteria:**
- [ ] Criterion
- [ ] `just lint && just test` passes

---

## Verification Checklist

Before marking as complete:
- [ ] All stories marked [x] in progress file
- [ ] `just lint` passes (ruff + mypy)
- [ ] `just test` passes
- [ ] No modifications outside owned paths
- [ ] Delivered tag written to progress file (see SKILL.md — never put the literal tag in templates)

## Handoff Notes

After this agent completes, other agents will have access to:
- [What downstream waves can import/use from this agent's work]
