# Stack Pro/Cons Matrix

Every layer has options behind one contract. **The default is the lowest-friction option that still demonstrates the concept. Switch only on a named trigger** — a specific signal (company preference, key/compute availability, time budget), never a vibe. Anything without a trigger stays on default.

Each table: **Option | Pros | Cons | Default? | Switch trigger**.

## Orchestration — contract: `Orchestrator`

Three decisions hide in this layer: the **topology** (the shape of the agent graph), the
**control-flow authority** (who picks the next step), and whether a **framework** owns the
loop. They are deliberated separately — see [deliberation-layers.md](deliberation-layers.md)
§1–2.

### Topology — the shape of the agent graph

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Router → specialists | Routing is unit-testable (an accuracy test ships), full trace hooks, zero planner tax | Routes fixed at design time; doesn't decompose novel tasks | **Yes** | — |
| Single agent + tool loop | Simplest stateful shape; already shipped (`run_tool_loop`); right for write-heavy/sequential work | Long contexts degrade; no specialization | **Yes** (for tool-using routes) | — |
| Fixed pipeline/DAG | Deterministic, reproducible, auditable; barely needs loop budgets | Rigid; re-plumb per workflow change | No | The workflow has >1 mandatory stage a human can draw at design time |
| Supervisor-worker | Only shape that handles genuinely dynamic subtasks; ~+90% on breadth research (Anthropic '25) | ~15× tokens; supervisor is the latency floor; budgets mandatory | No | Subtasks unknowable at design time AND read-heavy AND value tolerates ~15× cost |
| Handoff/swarm | Clean conversational domain transfer; ~20-line extension of the router loop | Decentralized control is hard to trace/test; degrades past ~8–10 agent types | No | Conversational domain-transfer *is* the product |
| Debate/ensemble | Visible deliberation as a product feature; judge panels useful for eval | N× cost with weak quality evidence vs CoT at matched compute; fragile termination signals | No | The deliberation itself is the demo — never as a quality lever; requires model tiering |

> Sync coupling: supervisor-worker's headline win is *parallel* subagents — the one topology
> benefit the sync mandate can't deliver. Sequential fan-out keeps sync but pays the token cost
> without the latency win.

### Control-flow authority — who picks the next step

The router is a registry layer (`Router` contract): select with `router: {impl: …}` in a
profile or `CHASSIS_ROUTER_IMPL` live; the orchestrator also takes an injected `specialists_map`
so a new route is an entry, not an elif.

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Rule/keyword router (code) | Zero deps, zero latency, deterministic, unit-testable accuracy | Brittle to paraphrase; ~5–10 route ceiling; keyword-bound | **Yes** | — |
| Embedding-similarity router | ~ms latency, handles paraphrase, offline; ~30 lines on the existing `Embedder` contract | Needs labeled utterances per route + threshold tuning | No | Eval shows paraphrase misroutes, or routes exceed ~5 |
| Constrained-enum LLM routing | Out-of-set answers impossible (structured output / forced tool choice); one cheap call | Key + ~1s latency; accuracy only measurable via an eval set | No | Routing needs conversational context or multilingual input; precondition: a routed eval set exists |
| ReAct planner loop | Handles genuinely open-ended step sequences | Untestable as a unit; loop/thrash failure modes; hard budgets mandatory | No | Step sequence unknowable at design time — and never for top-level routing |
| Plan-and-execute | Plan is inspectable/approvable before execution; fewer planner calls than ReAct | Two-tier model wiring; stale plans need re-plan logic | No | Dynamic multi-step sequencing AND approval gates on the plan are required |

### Framework — who owns the loop

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Custom (router + specialists) | Full explainability, zero framework debugging, trace bus hooks everywhere | You write the loop; no graph viz out of the box | **Yes** | — |
| LangGraph | Built-in graph visualization, checkpointing, ecosystem | Framework debugging under a clock; opinionated state model | No | They want graph viz, or are a LangGraph shop |
| CrewAI | Fast role-based multi-agent setup | Less control over the exact loop and tracing | No | Role-based agents are the explicit ask |

> AutoGen/AG2 is in maintenance mode (superseded by Microsoft Agent Framework, late 2025) —
> prefer LangGraph or MAF for new framework work. Framework adoption also pulls memory
> (checkpointer) and tracing into the framework — it re-decides more layers than this one.

## Budget & termination — what stops a loop (no contract; lives in the loop)

Bounded rounds ship (`config/defaults.py:TOOL_LOOP_MAX_ITERS`). This layer is barely contested
for code-routed pipelines and becomes mandatory the moment an LLM decides control flow or a
side-effecting tool exists. The canonical production failure is multi-agent ping-pong with no
shared done-state — round caps mitigate it; repetition detection catches it.

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Bounded rounds (shipped, 5) | Zero deps, deterministic, the universal floor — every framework ships one | Blind to cost-per-round variance; no signal *why* it stopped | **Yes** | — |
| Exact repetition detection | Catches the real failure mode (identical tool+args ping-pong); ~15 lines, warn-then-halt | Misses semantically-equivalent-but-reworded loops | No | Control flow moves off code-routing, or agents message each other |
| Per-query token budget | Bounds the actual resource; ~10 lines — `LLMResponse.usage` already exists in the contract | Offline adapters return empty `usage` — must degrade to round-counting | No | A paid-API profile faces unattended traffic (cron, public demo, batch) |
| Wall-clock timeout | Catches slow-provider pathologies round counts miss | Can truncate a legitimately slow final synthesis | No | A provider-latency incident is actually observed (per-call HTTP timeouts in adapters cover the realistic case first) |
| Gateway budget (LLM-proxy `max_budget` per key) | Real money cap independent of app bugs; covers loops you forgot to bound | A service to run — deployment-shape coupling | No | Multi-user/multi-project deployment on shared keys |
| HITL interrupt + checkpointed pause | The only real answer for approving side-effecting actions mid-run | Needs persistence + a serving shape that parks requests; fights sync | No | First side-effecting tool ships |

## LLM provider — contract: `LLM`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Provided cloud key (Anthropic/OpenAI) | Best quality, no local compute, fast | Costs money; dies if the key dies | **Yes** | — |
| Ollama (local) | No key, fully offline, free | Needs local compute/RAM; lower ceiling; slower | No | No key available, or the cloud key dies mid-demo |
| Azure / Bedrock | Enterprise compliance, existing contracts | More setup, region/quirk handling | No | They name a specific managed cloud |

### Model tier strategy — which roles get which model class

Tiering is pure config (the `LLM` Protocol is role-agnostic; a profile can carry a second slot)
— the cheapest-to-reverse decision in the stack. House rule: **strong where output is permanent
or user-facing synthesis; cheap where output is ephemeral control, judging, or summarization.**

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| One model everywhere | Zero config sprawl; one bill, one behavior to debug | Pays strong-model prices for summary/judge calls; judge shares identity with the synthesizer (self-preference bias) | **Yes** | — |
| Two static slots (strong + fast) | 60–80% cost cut in production practice; breaks judge/synthesizer identity; binding visible in the profile | One more profile slot + constructor param per consuming layer | No | Per-session cost is felt; or the eval judge is scoring its own synthesizer; or fast-path latency hurts |
| Learned router / cascade | Best published cost/quality frontier (~85% cut at ~95% quality) | Needs training data, calibration, and volume; a model artifact to own | No | Sustained production volume with a baselined eval set — never for a prototype |
| Local-only (Ollama-class) | $0 marginal cost; data never leaves the building | Lower ceiling everywhere, including synthesis | No | Data-residency constraint — already expressible as a whole-profile swap |

## Tool surface — contract: `ToolSpec`/`ToolCall` + `run_tool_loop`

The seam ships; tools never do. `ToolSpec.parameters` is raw JSON Schema — the lingua franca
every option below compiles to, so every exit stays cheap.

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Provider-native function calling (the shipped seam) | Zero deps, sync, traced, bounded; works on all three LLM adapters today | Tools live in-process — no sharing/discovery; each handler hand-written | **Yes** | — |
| MCP client bridge | Instant access to >10K maintained servers; foundation-governed, multi-vendor protocol | Async-only Python client (sync wrapper required); subprocess/HTTP lifecycle; third-party server trust is your problem | No | A maintained MCP server already does it and hand-writing would exceed ~a day; or the same tools must serve multiple hosts |
| MCP server (expose project tools outward) | Same handler functions, second transport; lets agent IDEs call project tools | Serves *external* agents — a different problem than this layer | No | Project handlers should be callable from Claude Code / IDEs |
| Framework tool registry | Signature→schema generation; built-in approval/deferred-tool machinery | An orchestration framework in disguise — displaces the loop and silently re-decides topology, control flow, and budgets | No | That framework was adopted for orchestration anyway — never for tools alone |
| Code execution / sandbox | Unbounded expressiveness; token-efficient at large tool counts | Heaviest safety story — isolation is mandatory, never in-process; deployment/key coupling | No | The task is literally running generated code, or tool count passes ~20 and definition bloat is measured |

> Side-effect policy: the first write/send/book verb activates, in order of cost — a
> confirmation wrapper at the `Handler` seam (~10 lines in a sync loop), per-tool guardrail
> policy, and hard budgets. The MCP annotation vocabulary (read-only / destructive /
> idempotent) is the house convention for flagging tool risk.

## Data contracts & structured output — `lib/contracts.py` + the `ToolSpec` seam

Two decisions: what the types are, and how the LLM is made to emit them. JSON Schema is the
settled wire format either way — every enforcement option compiles to it.

### Static types

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| stdlib dataclasses + Protocols | Zero deps, mypy-checked, offline tier works; production-proven for LLM transport | No runtime validation — malformed dicts fail downstream, not at the boundary | **Yes** | — |
| Pydantic at the HTTP boundary only | FastAPI requires it; validation exactly where input is untrusted | Must never back-propagate into `lib/contracts.py` | **Yes** (at that boundary) | A re-skin exposes an API surface |
| Pydantic in contracts | Runtime validation; auto-derived JSON Schema (no drift) | Leaks into every adapter signature; the contracts are frozen — this is a rewrite, not a switch | No | A layer must validate genuinely untrusted payloads beyond guardrails' scope — keep it inside that layer |
| msgspec / TypedDict | Fastest validation (msgspec); lighter typing (TypedDict) | Perf is meaningless next to LLM latency; no LLM-ecosystem integration | No | A *measured* serialization bottleneck (won't happen at this scale) |

### Enforcement — making the LLM emit the type

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Forced tool-use via the shipped `tools=` seam | Zero deps, zero contract changes; all three adapters; offline-fakeable; one bounded re-ask handles stragglers | Hand-written JSON Schema can drift from its dataclass; tool indirection is odd for pure extraction | **Yes** | — |
| Provider-native strict mode (`response_format`-class) | Grammar-level guarantee — schema-valid by construction, no retry loop | Not in the frozen `LLM` Protocol — a sanctioned contract addition is the named price | No | The forced-tool path empirically fails more than a bounded re-ask absorbs |
| Instructor | Best-in-class validation-retry-with-error-feedback; provider-uniform | Drags Pydantic into the calling layer; wraps clients the registry already abstracts | No | ≥3 structured-call sites need retry-with-feedback, or schemas visibly drift from their dataclasses |
| Outlines/XGrammar (direct) | True logits-level constraint on local models | Only applies to in-process inference — Ollama already exposes it server-side via `format=` | No | Raw in-process inference enters the stack |

## Inference pipeline design — no contract; lives inside a specialist

How one query becomes one answer — the stage decomposition *inside* a route. Distinct from
topology (which shapes the agent graph): this shapes a single agent's work. Each non-default
shape fixes one specific failure mode; pick by what the eval harness actually shows failing,
and note the shapes compose (a plan-then-write writer can itself be a staged pipeline; a
map-reduce reduce step can be best-of-N).

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Single-prompt synthesis (shipped specialists) | One call, one prompt — cheapest, fastest, simplest to trace | The prompt accretes competing concerns (content + tone + format + citation rules) until quality drops; all-or-nothing failure | **Yes** | — |
| Staged SoC pipeline (gather → transform → curate → format) | Each LLM stage owns one concern, one prompt, one fallback; deterministic stages are unit-testable; degradation is graceful (curate fails → annotate → top-N, the answer still ships) | More calls per answer; state must be plumbed between stages | No | The answer mixes prose with structured artifacts (curated citations, evidence exhibits, display metadata), or one prompt visibly accretes competing concerns |
| Plan-then-write (outline → expand) | A cheap planning call fixes global structure before any prose; the plan is inspectable/approvable; sections expand independently against assigned evidence | Two+ calls; a stale plan needs re-planning when evidence contradicts it; rigid skeletons can fragment voice | No | Outputs are long-form structured documents (reports, briefs, PRDs) where single-pass drafts lose global coherence |
| Map-reduce over sources | Handles input beyond any context window; per-source attribution falls out of the map step; deterministic split/merge; sequential maps keep sync | Cross-chunk context lost at boundaries; the reduce step can flatten nuance; latency scales with source count | No | Source material exceeds the context window, or per-source attribution is required (digest/synthesis scenarios) |
| Best-of-N + selection | Embarrassingly simple quality lift when variance is high; selection is deterministic for convergent answers (self-consistency vote) | N× cost per answer; for open-ended answers the judge-selector is the weak link (inherits judge biases) | No | Eval shows high answer variance — vote when answers are short/checkable, judge-select otherwise |
| Reflection (draft → critique → revise) | Catches rubric-detectable failures (ungrounded claims, missed requirements) before the user does | 2–3× cost; a critic sharing the author's prompt rubber-stamps — it needs its own rubric and ideally a different model | No | Eval shows quality failures a written rubric provably catches — never as a default "make it better" pass |

> The SoC rules that make any staged shape pay (proven in PROVE's QA pipeline): accumulate
> working state **out-of-band** of the conversation (parse tool results into typed state; don't
> make the model re-emit them); make every stage that *can* be deterministic deterministic
> (sort, filter, trim, assemble); tag every LLM call with its purpose for per-stage cost
> attribution; and never let the synthesis model write the structured section — code appends
> it. Couplings: stage boundaries are exactly where model tiers (LLM layer) and budgets
> (Budget & termination) bind, and each stage should emit on the trace bus.

## Embeddings — contract: `Embedder`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| all-MiniLM-L6-v2 (384-dim) | Tiny, fast, offline, great default | Lower retrieval quality than larger models | **Yes** | — |
| bge-small-en-v1.5 (384-dim) | Better quality, **same dim as MiniLM (free swap)** | Larger download | No | Want more quality and download time is fine |
| OpenAI text-embedding-3-small (1536-dim) | Strong quality, no local compute | Costs money; **different dim — see coupling** | No | No local compute available |
| Hashing (feature-hash, any dim) | Zero deps, deterministic, no model/download | Lexical overlap only, no semantics | No | Tests / CI / offline |

> Coupling: dim is frozen at ingest. MiniLM ↔ bge is a free swap (both 384). Switching to OpenAI (1536) after ingest requires a full re-ingest.

## Vector DB — contract: `VectorStore`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Qdrant | Production-grade, real ANN, scales independently, the "prod" story | Needs a running service (docker-compose) | **Yes** | — |
| Chroma (in-mem) | Zero services, runs in-process, trivial setup | Not the production story; memory-bound | No | Zero-service environment needed |
| FAISS (pure lib) | No service, fast, battle-tested | Lowest-level; you manage persistence/metadata | No | Zero-service and you want raw control |
| Memory (in-process) | Zero deps (no numpy), brute-force cosine | O(n) search, not persistent | No | Tests / CI / offline |

> Coupling: this choice drives deployment. Qdrant → docker-compose. Chroma/FAISS → single Dockerfile or bare process.

## Ingestion — no contract, deliberately

CHASSIS ships **no ingestion pipeline**. Loading and chunking are domain decisions — file
formats, chunk boundaries, metadata, dedup all depend on the corpus — and a pre-built pipeline
is the first thing every real project rips out. The seam is the contracts: produce `Chunk`s
however fits your data, then `embedder.embed(texts)` → `store.upsert(collection, chunks,
vectors)`. That's the whole interface.

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Hand-rolled loader (walk folder → fixed-window chunks, ~20 lines) | Zero deps, full control, fits any corpus quirk | You write it; naive chunk boundaries | **Yes — write your own** | — |
| LangChain / LlamaIndex loaders | Hundreds of formats and splitters out of the box | Heavy dependency for a loading step | No | Many formats needed right now |
| Unstructured / Docling | Layout-aware PDF/Office parsing, tables survive | Heavy install, slower | No | Real PDFs/Office docs where layout matters |

Best practices, regardless of loader:

- **Start at ~800-char chunks with ~15% overlap**; tune against eval scores, not intuition.
- **Stable chunk ids** (e.g. hash of source + offset) so re-ingest is idempotent.
- **Carry provenance** — `Chunk.source` (and `meta`) is what makes citations possible later.
- **Lock the embedder first** — dimension freezes when the collection is created (coupling #2).
- **Freshness is a re-run, not a pipeline.** Stable ids make `upsert` an overwrite for changed
  chunks; `store.delete(collection, ids)` removes chunks whose source disappeared (diff the id
  sets between runs). Scheduling the re-run — cron, CI, a watcher — is per-project, like the
  loader itself.

## Retrieval — contract: `Retriever` (+ optional `GraphStore`)

Default retrieval is vector-only over the `VectorStore`. A knowledge-graph option adds structural recall (vector hit → graph-expand to connected nodes) behind the same `Retriever` contract, via a `HybridRetriever` and a new optional `GraphStore`. See [extensibility.md](../guides/extensibility.md) Move 2 — this is the one deliberate pre-build contract addition.

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Vector-only | Simplest, one store, fewest moving parts | Misses structural/relational context | **Yes** | — |
| Hybrid + SQLite/NetworkX graph | Connected-evidence recall, in-process, zero service, graceful-degrade to vector | Two stores to keep in sync; Python-side traversal | No | The corpus has real structure (code, entities, citations) worth traversing |
| Hybrid + Neo4j graph | Native multi-hop + vector index in one engine, scales | A service to run; deployment weight | No | >100k chunks, or genuine multi-hop queries |

> Coupling note: the graph backend follows the same service-vs-in-process split as the vector DB. SQLite/NetworkX stays bare; Neo4j needs a service.

### Retrieval upgrades — no contract change (wrap or extend `Retriever`)

The consensus upgrade order: **rerank first, lexical+fusion second, everything else
case-by-case** — and only with the eval harness running; an upgrade you can't measure is a
vibe. All of these fit behind `retrieve(query, k)` as a wrapper or a sibling implementation.

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Reranker decorator (local cross-encoder) | Biggest quality jump per line of code (+17–40% on recall/MRR in benchmarks); rides the existing sbert extra; offline | Slow on CPU at latency-SLO scale; model download | No | The eval harness shows top-k precision is the measured bottleneck |
| Reranker decorator (API) | No local compute; slightly higher aggregate quality | Key + cost + network; must degrade gracefully to the inner order on failure | No | A key exists and local CPU latency hurts |
| BM25 + RRF hybrid | Fixes the exact-term/ID/code/name queries dense embeddings miss; RRF is ~60 stdlib lines (k=60, don't tune it) | A second index to keep in sync — unless the vector DB hosts sparse vectors server-side (Qdrant can; Chroma/FAISS/memory can't) | No | Eval shows lexical failures — names, codes, identifiers |
| Contextual retrieval (ingest-time) | Strongest documented failure-rate cut when stacked with the above | One LLM call per chunk at ingest; an ingestion *recipe*, not an adapter; breaks key-free ingest unless local | No | Chunks are ambiguous without document context AND an LLM budget exists at ingest |
| Agentic retrieval (rewrite / multi-hop loop) | Real gains on genuinely multi-hop questions; pure orchestration logic over existing contracts | Multiplies LLM calls per question; gains vanish on single-hop corpora | No | Eval failures are specifically multi-hop |
| Text-to-SQL grounding | The only option when the knowledge IS a relational database | ~10–31% real-world accuracy on enterprise schemas (vs 85–90% marketing); a *tool*, not a `Retriever`; DB coupling | No | The corpus is literally a database and questions are aggregations — enters as an orchestration tool with a constrained schema |

## Memory — contract: `Memory`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| In-process buffer + vector recall + overflow summary | No extra service, covers short + long term; the same anchored-compaction pattern vendors later productized | Lost on restart (not persistent); recalls raw turns, not distilled facts | **Yes** | — |
| File/SQLite-persisted sessions | Stdlib-only persistence; trivially inspectable; keeps deployment bare | Single-host; manual schema | No | Persistence across restarts is asked for and it's single-host |
| Redis-backed | Shared across processes | Another service to run | No | Cross-process / multi-worker session sharing |
| Extraction memory (Mem0-class) | Distilled facts beat raw-turn recall for personalization; large token savings | An LLM call per memory write — breaks the zero-key tier; benchmark claims are vendor-contested | No | Cross-session user-profile facts are needed AND an LLM call per turn is acceptable |
| Graph/temporal memory (Zep/Graphiti-class) | Temporal fact invalidation ("true until X"); provenance per fact | Graph DB service + LLM extraction per episode — the heaviest option | No | Queries are genuinely temporal/relational AND retrieval already earned a graph service (share it) |
| Framework checkpointer / durable execution | Resumability, HITL pauses, replay debugging | Couples memory to the framework; true durability (Temporal-class) is a server + deterministic-workflow programming model that fights sync | No | Already committed to that framework; or workflows must survive process death mid-run and re-running steps is unsafe |

> Multi-agent shared state is a pattern choice, not a product: **scoped handoff context**
> (self-contained task in, typed result out) is the converged default; a blackboard only for
> specialist webs with unknown processing order; shared mutable state is the documented
> anti-pattern. Coupling: memory recall embeds into the vector store, so the embedder-dim
> freeze covers the memory collection too.

## Guardrails — contract: `Guardrail`

The base ships a passthrough stub, not a policy — what to enforce is domain-specific. A project registers its own rail under `guardrail` and selects it in a profile; the orchestrator's block seam already honors a failing verdict.

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Passthrough stub | Zero policy baked in; the base stays domain-neutral | Enforces nothing until a project adds a rail | **Yes** | — |
| Project-specific rules (heuristics + LLM judge) | Tailored, transparent; heuristics run <10ms; judge rides the existing `LLM` contract; the production-proven first escalation | You write and maintain them; judge adds an LLM call per checked side | No | The domain needs input/output enforcement — escalate here first, not to a library |
| Provider moderation endpoint | Free, ~80ms, multimodal harm categories | Injection-blind by design (harm content only); data leaves the building | No | Harm-content liability and a cloud key is already in the profile — always paired with heuristics |
| Classifier rails (Prompt Guard-class) | Offline-capable, injection-specific coverage moderation lacks; tens of ms | torch-class extra; double-digit miss rates on paraphrased attacks | No | Prompt injection is a stated threat and the deploy must stay offline |
| Guardrails AI | Validator-hub composition, sync API, failure strategies | Hub validators pull their own ML models (CPU-seconds) or need a remote-inference key | No | They want a named library |
| NeMo / OpenAI Guardrails | Declarative/bundled rail pipelines, enterprise pedigree | Heavy deps; async-first internals fight the sync mandate; LLM self-check rails cost two extra LLM round-trips; default LLM-judge checks have been demonstrably bypassed | No | Enterprise/declarative rails are the explicit ask |

> Three structural notes: (1) an LLM-judge rail must be a **different model family** than the
> answerer — same-model judges share the guarded model's blind spots and are bypassable.
> (2) Tool-call vetting is *not* this contract's job: per-tool policy (allowlists, approval
> tiers, fail-closed on empty allowlist) lives at the `run_tool_loop` seam and becomes
> mandatory at the first side-effecting tool. (3) A rail can pass-with-revision —
> `Verdict(passed=True, revised=…)` replaces the answer text (redaction), keeping citations;
> `passed=False` still withholds entirely.

## LLM eval — contract: `Evaluator`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Custom RAGAS-style + judge | Shows you understand the metrics, not just the import; no extra dep; offline heuristics keep CI keyless | You implement faithfulness/relevance/precision | **Yes** | — |
| RAGAS (library) | Named, citable metrics; now ships agent-trajectory metrics (tool-call accuracy, goal accuracy) | Dependency (pulls langchain-core); judge metrics need a key | No | Named metrics demanded, or trajectory metrics needed faster than writing them |
| DeepEval | Test-style assertions, CI-friendly; active agent-eval coverage | Another framework's conventions; platform upsell in the docs | No | Eval-as-tests is the explicit ask |
| promptfoo | Best packaged PR-diff regression workflow (before/after comments, caching) | A Node tool in a Python repo; acquired by OpenAI (2026-03) — governance risk for a neutral skeleton | No | Prompt-diff PR comments are wanted and a Node binary is acceptable |

> Judge notes: position, verbosity, and self-preference biases are well-documented — mitigate
> with swap-and-average ordering, criteria-anchored rubrics, and a judge from a **different
> model family** than the generator. Trajectory eval (scoring the multi-step run, not just the
> answer) takes the per-run trace JSONL as its input — the bus below is already the artifact.
> CI pattern: heuristic metrics run keyless on every gate; judge metrics are an opt-in keyed
> job; regression = delta against a baselined run.

## Tracing & observability — the `TraceBus` seam (`lib/trace.py`)

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Homegrown TraceBus (ring + JSONL) | Zero deps, offline, single emit point, the UI polls it, JSONL doubles as eval evidence | No cross-run UI; no distributed context; the schema is yours to maintain | **Yes** | — |
| OTel GenAI-semconv sink | Vendor-neutral standard; one adapter class on the bus's single `emit()` — not a re-instrumentation | Agent-span conventions still experimental (attribute churn); ~5 packages | No | The conventions reach Stable, or a client mandates OTLP |
| Arize Phoenix (self-host) | Lightest platform self-host (one container, SQLite); OTel-native | Another process + the OTel deps to feed it | No | A cross-run trace UI / waterfall view is needed beyond the dashboard tab |
| Langfuse (self-host or cloud) | Best full-featured OSS platform; true data ownership; team annotation workflows | v3 self-host is four services (ClickHouse/Redis/S3/Postgres) — heavier than CHASSIS itself | No | A *team* needs shared annotation/scoring workflows |
| Hosted platforms (LangSmith / Braintrust / Weave) | Zero-config, polished, strong CI gating; keyless-degrade integration is a proven pattern | Hosted-first; self-host is enterprise-only; breaks the offline tier | No | The client already runs that platform |

> The homegrown bus stops being enough when (any one): traces must be compared *across* runs
> in a UI; more than one person debugs concurrently; real production traffic needs
> alerting/sampling; an OTel mandate appears. Until then the ring + JSONL covers debug, demo,
> and eval evidence. Two rules survive any choice: every component emits through the one bus
> (or the cheap OTel bridge is lost), and hosted anything lazy-inits behind a key check so the
> offline tier never notices.

## UI — contract: the four-tab dashboard reads the trace bus

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Gradio | Fastest to a working dashboard, trivial polling | Less layout control | **Yes** | — |
| Streamlit | More layout control, familiar | Rerun model can fight live state | No | You need finer layout control |
| FastAPI + React | Full control, production-grade | Far more build time | No | Only with spare time |

## Theming — `tokens.json` → CSS custom properties injected into the UI

Makes the demo look intentional instead of default-Gradio-grey. A single `tokens.json` is the source of truth; `app/ui/theme.py` loads it and injects CSS variables into Gradio's `Blocks(css=...)`. One `THEME` flag selects the palette; the node-color tokens double as the trace-event color encoding. Source themes live in `../THEMES/`.

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| METHODPROOF (SHOMEN/KINMYAKU) | Production-proven, dual light/dark, 5-color node palette maps to trace events, sharp/disciplined | Opinionated, formal | **Yes** | — |
| Other workspace theme (ĀNUENUE, SHINKAI, …) | Same token shape, different mood (spectral, deep-sea, etc.) | One more palette to port | No | The domain wants a distinct aesthetic |
| Default Gradio (no theme) | Zero work | Reads as a prototype, not a product | No | Throwaway/internal-only demo |

> Keep it to one default theme + the swap mechanism. Porting all eight workspace themes is YAGNI.

## Deployment — driven by the vector DB choice

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| docker-compose (app + Qdrant) | Mirrors prod, isolates the service | Two containers, slower cold start | **Yes** (with Qdrant) | — |
| Single Dockerfile | One image, simple | No separate vector service | No | Chroma/FAISS chosen |
| Bare uvicorn | Fastest to launch, no Docker | Least reproducible | No | Chroma/FAISS chosen and Docker is overkill |

## The two couplings that constrain combinations

Most layers combine freely. Two do not:

1. **Vector DB → deployment.** Qdrant needs a service (compose); Chroma/FAISS run in-process (Dockerfile or bare). Decide the vector DB first.
2. **Embedder dim → ingest.** Dimension is frozen when a collection is created. MiniLM ↔ bge is free (both 384); OpenAI (1536) after ingest means re-ingest. Lock the embedder before ingesting.

Decide vector DB and embedder before anything else; the rest you can flip on a trigger without consequence.
