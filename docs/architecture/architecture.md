# Architecture

CHASSIS is a base repo for sophisticated multi-agent systems. It is not a single app. Every layer sits behind a contract and is selected by config, so a new project re-skins the base instead of rewriting it.

## The flexibility mechanism, in one sentence

`lib/contracts.py` defines what each layer must do, the `lib/*/` adapters implement it three ways, a registry picks one from config, and named profiles switch a whole backend with a single flag.

Four moving parts:

1. **Contracts** (`lib/contracts.py`) — Protocols + shared dataclasses. The only coupling allowed between layers. Frozen before the build; nothing imports a concrete class directly.
2. **Adapters** (`lib/*/`, `app/*/`) — concrete implementations of a contract (e.g. three vector stores, three LLM providers). Each is blind to the others.
3. **Registry** (`lib/registry.py`, *deferred*) — a factory mapping a config string to a concrete class. Swapping Qdrant for Chroma is a config change, not a code change.
4. **Profiles** (`config/profiles/*.yaml`, *deferred*) — named whole-stack presets. `CHASSIS_PROFILE` picks one; per-layer env vars override it for live pivots.

## Repo map

```
lib/
  contracts.py      Protocols + dataclasses (frozen)            [present]
  registry.py       config string -> concrete impl             [deferred]
  trace.py          TraceEvent bus: JSONL + ring buffer         [deferred]
  llm/              adapters: openai, anthropic, ollama         [deferred]
  embeddings/       adapters: sbert (minilm/bge), openai        [deferred]
  vectorstore/      adapters: qdrant, chroma, faiss             [deferred]
app/
  orchestration/    router + specialists + orchestrator loop    [deferred]
  memory/           short-term buffer + long-term recall        [deferred]
  guardrails/       input + output + LLM judge                  [deferred]
  eval/             metrics + LLM-as-judge + runner             [deferred]
  ui/               dashboard, tabs read the trace bus          [deferred]
  api/              JSON endpoints over the orchestrator seam    [present]
config/
  settings.py       env-driven config; resolves impls           [deferred]
  defaults.py       centralized tuning knobs (k, windows, ports) [present]
  profiles/         named stack presets                          [deferred]
```

There is deliberately no ingestion package. Loading and chunking are per-project decisions
(see [stack-matrix.md](../reference/stack-matrix.md), Ingestion); the seam is the contracts —
produce `Chunk`s, `embedder.embed`, `store.upsert`.

## The trace bus

Everything interesting emits a `TraceEvent` to a single sink (`lib/trace.py`). The sink does two things:

1. Appends to `runs/{run_id}.jsonl` — post-hoc debugging and eval evidence.
2. Pushes to an in-memory ring buffer (last 500 events) that the UI polls.

The ring buffer is a process singleton written by component threads and read by the UI threadpool, so it is a `collections.deque(maxlen=500)` behind a `threading.Lock`. UI tabs read it on a timer tick and filter by `component` prefix. No websockets.

Keep the event taxonomy small (~8 types): `route_decision`, `retrieval`, `memory_recall`, `guardrail_verdict`, `llm_call`, `answer`, `eval_score`, `error`.

The payoff: each UI tab is just a filtered view of one stream. The Chat tab is events where `component in {router, specialist.*}`; the Guardrails tab is `component.startswith("guardrail")`. The logs, the UI, and the demo narrative all read the same events.

## Life of a question

```
query
  -> guardrail.check_input        (block on length / injection / PII)
  -> router.route                 (retrieval | synthesis | chitchat)
  -> memory.context               (recent window + long-term recall)
  -> specialist                   (retrieval/synthesis) OR direct LLM (chitchat)
       -> retriever.retrieve      (vector search)
  -> guardrail.check_output       (schema + grounded-in-context)
  -> Answer                       (text + route + citations + contexts)
```

Every arrow emits a `TraceEvent`. The orchestrator's `handle(query) -> Answer` is the one seam the UI and eval both consume; `Answer.contexts` and `Answer.text` are exactly what an `EvalRow` needs, so evaluation reuses the same output with no glue.

## The two couplings (the only cross-layer constraints)

Everything else is independently swappable. These two are not:

1. **Vector DB drives deployment.** Qdrant needs a running service (docker-compose). Chroma and FAISS run in-process (a single Dockerfile or a bare process). Decide the vector DB first; deployment follows from it.
2. **Embedder dim is frozen at ingest.** A collection bakes in its vector dimension at creation, so an embedder swap is only safe *before* ingestion. all-MiniLM-L6-v2 and bge-small-en-v1.5 are both 384-dim (free swap, either direction). OpenAI `text-embedding-3-small` is 1536-dim — switching to it after ingest silently breaks search and requires a full re-ingest. Lock the embedder before ingesting.

## Frozen contract types

Shared dataclasses and Protocols live in `lib/contracts.py`.

| Type | Kind | Role |
|------|------|------|
| `Message` | dataclass | one chat message (role + content) |
| `LLMResponse` | dataclass | LLM output (text, model, token usage, requested tool calls) |
| `ToolSpec` | dataclass | a tool offered to the model (name, description, JSON-Schema parameters) |
| `ToolCall` | dataclass | one tool invocation the model requested (id, name, arguments) |
| `Chunk` | dataclass | a unit of ingested text (id, text, source, meta) |
| `SearchResult` | dataclass | a chunk plus its similarity score |
| `GraphNode` | dataclass | a node in the optional knowledge graph (id, kind, meta) |
| `GraphEdge` | dataclass | a directed edge between two graph nodes (source_id, target_id, kind) |
| `Turn` | dataclass | one conversational turn with a timestamp |
| `MemoryContext` | dataclass | recent window + recalled hits + optional summary |
| `Verdict` | dataclass | a guardrail decision (passed, stage, reasons, optional revised text) |
| `EvalRow` | dataclass | one eval record (question, ground truth, answer, contexts, scores) |
| `Answer` | dataclass | orchestrator output (text, route, citations, contexts) |
| `TraceEvent` | dataclass | one event on the trace bus |
| `LLM` | Protocol | `chat(messages, tools=) -> LLMResponse`; tool loop in `app/orchestration/tools.py` |
| `Embedder` | Protocol | `dim`, `embed(texts) -> vectors` |
| `VectorStore` | Protocol | `ensure_collection`, `upsert`, `delete`, `search` |
| `GraphStore` | Protocol | optional: `upsert(nodes, edges)`, `neighbors(node_id)` for graph-expand retrieval |
| `Retriever` | Protocol | `retrieve(query, k) -> SearchResult[]` |
| `Router` | Protocol | `route(query) -> str` — control-flow authority; `KeywordRouter` default, registry-selectable |
| `Tracer` | Protocol | `emit(component, event, **payload) -> TraceEvent` — the trace seam `TraceBus` implements |
| `Orchestrator` | Protocol | `handle(query) -> Answer` |
| `Memory` | Protocol | `add(turn)`, `context(query) -> MemoryContext` |
| `Guardrail` | Protocol | `check_input`, `check_output -> Verdict` |
| `Evaluator` | Protocol | `run(rows) -> EvalRow[]` |

See [extensibility.md](../guides/extensibility.md) to add an adapter or a layer, and [stack-matrix.md](../reference/stack-matrix.md) for the per-layer option trade-offs.
