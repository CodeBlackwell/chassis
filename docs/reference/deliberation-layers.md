# Deliberation layers — where an agent-orchestration stack gets decided

Companion to the [stack matrix](stack-matrix.md). The matrix answers *"which option for this
layer?"*; this doc answers the prior question: *"which layers need deliberating at all for this
problem?"* Every layer below now has a researched option matrix in the stack matrix — layers
1–2 under Orchestration (Topology / Control-flow authority), 3 under LLM provider (Model tier
strategy), 4 under Tool surface, 5 under Retrieval (upgrades table), 6 under Memory, 7 under
Data contracts & structured output, 8 under Guardrails, 9 under Budget & termination, 10 under
LLM eval + Tracing & observability, 11 under Inference pipeline design.

Eleven layers carry a real stack decision. The working claim: **most have a boring default, and
any given problem makes only two or three of them contested.** The fast path to a sound design
is to enumerate all eleven, accept defaults with one-line justifications, and spend the argument
time on the contested ones. Each layer below maps to a CHASSIS seam, so a decision here is a
profile line, not a rewrite.

## The eleven layers

Each entry: the question, the option spectrum (lightest → heaviest), what in the situation
decides it, and the CHASSIS default.

### 1. Orchestration topology — what shape is the agent graph?

- Spectrum: single agent + tools → router → specialists → fixed pipeline/DAG →
  supervisor-worker → debate/ensemble.
- Decider: **is the workflow knowable at design time?** If a human can draw the flowchart,
  encode it as code and skip the planning tax. Supervisor-worker earns its complexity only when
  subtasks are genuinely dynamic; debate only when answer quality justifies N× cost.
- CHASSIS default: router → specialists (`Orchestrator` contract, `app/orchestration/`).

### 2. Control-flow authority — who decides the next step?

- Spectrum: deterministic code (keyword/rule router) → cheap LLM as classifier → full LLM
  planner loop (ReAct-style).
- Decider: predictability vs. open-endedness. Code-routed control flow is debuggable and
  testable (the shipped router has an accuracy test; a planner can't have one). The single
  biggest reliability decision in the system, and the most commonly over-engineered.
- CHASSIS default: code-routed (`app/orchestration/router.py`).

### 3. Model tier per role — one model, or strong-where-it-counts?

- Spectrum: one model everywhere → strong for synthesis + cheap for routing/judging →
  local/offline only.
- Decider: cost-per-query × call volume, latency budget, and whether data may leave the
  building. Routing and judging are classification — they don't need the expensive model.
- CHASSIS default: one configured `LLM` per profile; the contract makes per-role mixing a
  registry/profile change.

### 4. Tool/action surface — does the system act, or only answer?

- Spectrum: none (pure RAG) → read-only tools (search, lookup) → side-effecting actions
  (write, send, book).
- Decider: the problem statement's verbs. The first side-effecting tool inherits confirmation
  flows, idempotency, and a heavier guardrail story — price that before accepting it.
- CHASSIS default: none. The seam is `ToolSpec`/`ToolCall` on the `LLM` contract plus
  `run_tool_loop` (`app/orchestration/tools.py`); tools and handlers are per-project.

### 5. Knowledge/retrieval layer — what grounds the agents?

- Spectrum: nothing → vector RAG → hybrid graph-RAG → structured (SQL/API) → mixed.
- Decider: corpus shape. Prose → vector. Entities-and-relations → graph. Tables → query them,
  don't embed rows. **The two couplings live here** — vector DB drives deployment, embedder dim
  freezes at ingest — the only decisions in the stack that aren't cheaply reversible, so they
  go first.
- CHASSIS default: vector-only `SimpleRetriever`; `GraphStore` contract in place for hybrid.

### 6. State and memory — what do agents remember, and who shares it?

- Spectrum: stateless → session window → window + long-term recall → persistent/shared store →
  shared blackboard between agents.
- Decider: conversation length, plus the multi-agent twist: do agents coordinate through shared
  state or passed messages? Shared mutable state is where multi-agent systems rot — default to
  passing results explicitly.
- CHASSIS default: window + vector recall + overflow summary (`app/memory/buffer.py`).

### 7. Inter-agent data contracts — what travels between components?

- Spectrum: free-form text → typed structures at every seam.
- Decider: parallelism and team size. Free text between agents is fine for two components and
  fatal for five. The principle: **agents may speak prose to the user, never to each other.**
- CHASSIS default: typed everywhere — `Answer`, `MemoryContext`, `Verdict`, `SearchResult` in
  `lib/contracts.py`. This is the repo's foundational bet.

### 8. Guardrails — where do the rails sit, and how strict?

- Spectrum: none → input + output rails on the orchestrator → per-tool policy → LLM-judge rail.
- Decider: domain regulation and audience. A demo for engineers needs a passthrough; a
  regulated-domain assistant makes this layer the centerpiece. Position matters as much as
  policy: an output rail must see the *final* answer (which is why token streaming fights this
  architecture).
- CHASSIS default: wired seam, passthrough policy (`app/guardrails/`) — policy is per-project.

### 9. Budget and termination — what stops a loop?

- Spectrum: bounded rounds → token/cost budgets → timeouts → loop/repetition detection.
- Decider: layers 1–2. Any LLM-decides-next-step design makes this mandatory — unbounded agent
  loops are the canonical production failure. A fixed pipeline barely needs it.
- CHASSIS default: bounded rounds (`config/defaults.py:TOOL_LOOP_MAX_ITERS`); sync everywhere
  keeps every call on a visible stack.

### 10. Observability and eval — how do you see it think, and prove a change helped?

- Spectrum: logs → structured per-step trace events → replayable runs + a baselined eval set.
- Decider: none — **this layer is never contested.** Multi-agent systems are undebuggable
  without per-decision traces, and upgrades are vibes without a baseline. Trace and baseline
  first, always.
- CHASSIS default: the `TraceEvent` bus every component emits to (`lib/trace.py`) + the eval
  harness (`app/eval/`).

### 11. Inference pipeline design — how one answer gets assembled

- Spectrum: single-prompt synthesis → staged separation-of-concerns pipeline (gather →
  deterministic transform → scoped curate → deterministic format) → plan-then-write →
  map-reduce over sources → best-of-N + selection → reflection/self-critique.
- Decider: **the failure mode the eval actually shows.** One kind of output (a prose answer) →
  one call. Mixed prose + structured artifacts (citations, exhibits) → staged SoC. Long-form
  documents losing global coherence → plan-then-write. Input beyond the context window or
  per-source attribution → map-reduce. High answer variance → best-of-N. Rubric-detectable
  quality failures → reflection. The shapes compose; across all of them the same rules hold —
  one concern per LLM stage, deterministic wherever possible, working state out-of-band of the
  conversation, and the structured section appended by code, never written by the synthesis
  model. Distinct from layer 1: topology shapes the agent *graph*; this shapes one agent's work
  *inside* a route.
- CHASSIS default: single-call specialists (`app/orchestration/specialists.py`). The staged
  pattern is proven in-workspace (PROVE's QA pipeline: bounded gather loop → sort → curate with
  fallback → format, every LLM call purpose-tagged for per-stage cost attribution).

## Which layers become contested, by scenario family

Everything not listed stays on default.

| Scenario family | Contested layers | The deliberation |
|---|---|---|
| Corpus Q&A (handbook, legal, code) | 5 | chunking + the two couplings; all else defaults |
| Support/escalation bot | 1, 2 | does low retrieval confidence trigger a route? code or LLM decides? |
| Triage/routing (tickets, email) | 2, 3 | the router *is* the product — rules vs cheap classifier |
| Acting assistant (book, file, notify) | 4, 8, 9 | side-effects → confirmations, per-tool rails, hard budgets |
| Regulated domain (medical, finance) | 8, 3 | rails are the centerpiece; can data leave the building? |
| Cross-document synthesis/digest | 1, 6, 11 | fan-out topology; how partial results aggregate |
| Evidence-backed answers (citations, exhibits, audit trails) | 11, 7 | staged assembly — the model writes prose, code assembles the evidence section |
| Long-running assistant | 6 | recall vs window vs persistence |
| Structured-data Q&A | 5, 4 | retrieval is *wrong* here — schema-grounded query tool instead |
| Entity/relationship corpus | 5 | vector vs graph-hybrid; does the corpus earn a graph? |
| "Compare configs / improve quality" | 10, 3 | the eval harness is the product; judge model choice |

## Building on this doc

- A new scenario family → one table row naming its contested layers.
- A new deliberation layer → a numbered section here **and** (if it becomes a seam) a contract +
  registry slot per [extensibility.md](../guides/extensibility.md) Move 2.
- Concrete tool choices for a layer belong in the [stack matrix](stack-matrix.md)'s option
  tables, not here — this doc decides *whether* a layer is contested, the matrix decides *what
  wins it*.
