# CHASSIS

**An unopinionated, time-saving skeleton for multi-agent RAG — optimized for rapid
prototyping.** Define the seams once, then swap anything behind them — model provider, search
backend, agent loop — with one config flag instead of a rewrite.

Most RAG starters hard-wire their stack, and every architectural decision becomes permanent the
moment something imports it. CHASSIS inverts that: `lib/contracts.py` freezes *what each layer
must do* as small Protocols, adapters implement them, a registry resolves the implementation from
a named profile at startup, and an env var can override any single layer without touching the
profile. The result is a base you re-skin per project, where the stack is data, not plumbing.

```
contracts (frozen Protocols)  ──implemented by──►  adapters (lib/*, app/*)
        ▲                                              │
   everything codes                          registry resolves one
   against these                             from config, lazily
        │                                              ▼
   profiles (config/profiles/*.yaml)  ◄──overridable── CHASSIS_<LAYER>_IMPL env
```

## Try it in sixty seconds — no keys, no services, no heavy deps

The `memory` profile runs the entire loop (route → retrieve → answer → trace → eval) in-process
with zero external dependencies:

```bash
just setup
CHASSIS_PROFILE=memory just dev # four-tab dashboard on :8000
```

Loading documents is yours by design — CHASSIS deliberately ships **no ingestion pipeline**
(step 1 of the walkthrough shows the three-call seam any loader plugs into). Then point the
stack at a real backend by changing one word — `CHASSIS_PROFILE=qdrant-local` — or pivot a
single layer live: `CHASSIS_VECTORSTORE_IMPL=chroma`.

## The stack is a config file

A profile names an implementation for every seam. Side by side, the offline profile and a
production-shaped one differ only in their `impl` values:

```yaml
# config/profiles/memory.yaml          # config/profiles/qdrant-local.yaml
llm:         {impl: ollama}            llm:         {impl: anthropic, model: claude-sonnet-4-6}
embedder:    {impl: hashing}           embedder:    {impl: minilm}
vectorstore: {impl: memory}            vectorstore: {impl: qdrant}
```

| Seam | Contract | Ships working | Also wired in the registry |
|------|----------|---------------|----------------------------|
| Language model | `LLM` | Ollama (local), with a no-LLM extractive fallback | Anthropic, OpenAI |
| Embeddings | `Embedder` | feature-hashing (zero-dep) | MiniLM, bge, OpenAI |
| Vector search | `VectorStore` | in-process cosine | Qdrant, Chroma, FAISS |
| Retrieval | `Retriever` | vector-only | hybrid graph-RAG (`GraphStore` contract in place) |
| Agent loop | `Orchestrator` | router → specialists, fully traced | framework swap on a named trigger |
| Conversation state | `Memory` | window + long-term vector recall + overflow summary | Redis on a named trigger |
| Safety rails | `Guardrail` | a wired seam with a passthrough stub — policy is per-project, never baked into a base | Guardrails AI / NeMo |
| Scoring | `Evaluator` | RAGAS-style metrics + optional LLM judge + seed-set generator | RAGAS / DeepEval |

Defaults are deliberate: the lowest-friction option that still demonstrates the concept, with the
production option one flag away. The per-layer trade-offs and the trigger that justifies each
switch live in [the stack matrix](docs/reference/stack-matrix.md). The same principle covers the
numbers: every tunable int/string (retrieval `k`, memory window, token budgets, eval thresholds,
ports) lives centralized in `config/defaults.py`, with profiles overriding per stack.

## Walkthrough — from a folder of documents to a deployed assistant

The shape CHASSIS is optimized for: **an assistant over a private corpus** — a team handbook,
product docs, a contract archive, a research pile. The domain changes; the sequence doesn't.

**1 — Load the corpus, your way.** CHASSIS deliberately ships **no ingestion pipeline**.
Loading and chunking are domain decisions — formats, chunk boundaries, metadata all depend on
the corpus — and a pre-built loader is the first thing a real project rips out. What the base
ships is the seam, three contract calls that any loader plugs into, from a ten-line folder
walker to a layout-aware Docling pipeline:

```python
from config.settings import Settings

settings = Settings.load("memory")
embedder, store = settings.build("embedder"), settings.build("vectorstore")

chunks = my_loader("corpora/handbook")   # your code: yield Chunk(id, text, source)
store.ensure_collection("chassis", embedder.dim)
store.upsert("chassis", chunks, embedder.embed([c.text for c in chunks]))
```

> **Behind the scenes:** `Settings.load("memory")` reads the profile YAML and the registry
> lazy-imports only the implementations it names — `HashingEmbedder`, `MemoryStore` — nothing
> else is even imported. **This is the moment coupling #2 engages:** the collection's dimension
> is now fixed to this embedder family. Loader options (LangChain/LlamaIndex, Unstructured,
> Docling, hand-rolled) and chunking best practices live in the
> [stack matrix](docs/reference/stack-matrix.md)'s Ingestion section.

**2 — Talk to it, and watch it think.**

```bash
CHASSIS_PROFILE=memory just dev         # dashboard on :8000
```

Ask in **Chat**, then check **Sources**: did retrieval return the right chunks, and do the
citations actually ground the answer? The trace tells you *where* a bad answer went wrong —
routing, recall, retrieval, or synthesis — instead of leaving you to guess.

> **Behind the scenes:** `python -m app.ui` assembles the same stack and hands it to Gradio with
> CSS variables injected from `tokens.json`. Every chat turn is one `handle()` call; every tab
> is a different read of the same `TraceBus` ring buffer (a 500-event deque behind a lock).
> Memory records both sides of each turn twice — into a sliding window for short-term context,
> and embedded into its own vector collection so a fact from turn 1 is still findable at
> turn 40, after the window has long evicted it.

**3 — Put a number on it before upgrading anything.** Generate a gold set from your chunks and
score a baseline:

```python
from app.eval.dataset import generate
from app.eval.runner import answer_rows

rows = evaluator.run(answer_rows(orchestrator, generate(chunks, n=20)))
```

This baseline is the point of the step: every upgrade after it is measured, not vibes.

> **Behind the scenes:** offline, the generator derives a question + reference answer from each
> chunk (degenerate but consistent — fine for a baseline); given an LLM it writes a real exam
> instead. The eval runner replays every question through the same orchestrator the Chat tab
> uses — not a separate code path — and `RagasEvaluator` scores each answer for lexical
> faithfulness (is it grounded in the retrieved context?), answer relevance, and context
> precision, each in `[0,1]`. The scores are honest about their nature: cheap lexical proxies
> by default, an LLM-judge column when a model is available. Wire this loop into
> `build_app(eval_fn=...)` and the dashboard's **Eval** tab runs it on demand.

**4 — Decide the two couplings, then graduate the stack.** Lock the embedder (dimension freezes
at ingest) and pick the vector DB (it drives deployment) — then the upgrade is install + flag:

```bash
uv sync --extra embeddings-sbert --extra vectorstore-qdrant --extra llm-anthropic
just services                            # Qdrant container
# re-run your loader under the new profile — a fresh 384-dim collection
CHASSIS_PROFILE=qdrant-local just dev
```

Same corpus, same questions, same eval set — now with semantic retrieval and synthesized
answers. Compare against step 3's numbers to see what the real stack actually bought you.

> **Behind the scenes:** the extras exist because every adapter lazy-imports its SDK — the base
> install never carries what the profile doesn't use; `uv sync --extra …` supplies the three
> SDKs the new profile names. The registry now resolves `SbertEmbedder` (384-dim MiniLM),
> `QdrantStore` (talking to the container `just services` started), and `AnthropicLLM`. The
> re-ingest is not ceremony — it's coupling #2: a 384-dim collection must be built fresh; the
> old one can't be reused. And the specialists upgrade themselves from extractive to
> LLM-synthesized answers purely because `llm` is no longer `None` — no orchestrator change,
> same trace shape, so step 3's eval comparison is apples to apples.

**5 — Make it yours.** Write the guardrail policy your domain needs (the seam is wired and the
orchestrator already honors a blocking verdict — implement `Guardrail`, add one registry line,
flip `guardrail: {impl: ...}` in the profile), swap the theme token file, and rename per the
[re-skin guide](docs/guides/extensibility.md).

> **Behind the scenes:** `handle()` already calls `check_input()` before routing and
> `check_output()` before returning, and short-circuits on a failing `Verdict` — the shipped
> `PassthroughGuardrail` simply always passes. Your rail is two methods returning `Verdict`s;
> the registry line makes it selectable; the profile selects it. Nothing else in the system
> knows or cares that enforcement appeared.

**6 — Ship per the coupling.** Qdrant → the included docker-compose (prod variant puts Caddy in
front); in-process store → single Dockerfile or a bare process.

> **Behind the scenes:** the Dockerfile takes an `EXTRAS` build arg and installs only the
> adapter groups the deployed profile needs — the image mirrors the profile, like everything
> else. The prod compose file keeps the app and Qdrant on an internal network with Caddy as the
> sole public entrypoint; the dashboard you ship is the same `python -m app.ui` from step 3.

Everything here is reversible except the two decisions in step 4 — which is why it's the only
step that asks you to *decide* rather than default.

## Watch it think

Observability is structural, not bolted on. Every component emits `TraceEvent`s to a shared bus
(ring buffer + per-run JSONL), so one question leaves a legible trail:

```
guardrail.input ─► router ─► memory ─► retrieval ─► specialist ─► guardrail.output ─► answer
```

The dashboard (`just dev`) puts that front and center — **Chat** with cited sources, **Sources**
showing what retrieval actually returned, **Guardrails** verdicts, and **Eval** scores, all
reading the same trace bus, themed via a single `tokens.json`.

## Judge it, don't vibe it

`app/eval/` generates a gold set from your chunks, runs the questions through the orchestrator,
and scores faithfulness / answer-relevance / context-precision — offline by default, with an
LLM-as-judge column when a model is available.

## Two couplings you can't config away

Honesty about the limits of swap-anything:

1. **The vector DB drives deployment.** Qdrant needs a service (docker-compose ships for it);
   Chroma/FAISS/memory run in-process (single Dockerfile or bare).
2. **Embedding dimension is frozen at ingest.** MiniLM ↔ bge is a free swap (both 384-dim);
   moving to OpenAI's 1536 afterwards means re-ingesting.

Decide those two first; everything else stays reversible.

## Built by an army, gated all the way

The repo ships its own build method: `scripts/ralph.py` runs autonomous agents solo or in
parallel waves with lint/test gates between waves and three-layer completion verification, fed by
PRD bundles under `prds/` and bracketed by a research-and-audit agent suite (`.claude/agents/`)
that turns an assignment into an options report before code, and audits the integrated result
after. See the [runbook](docs/runbooks/ralph-army.md).

## Docs

| | |
|---|---|
| [Architecture](docs/architecture/architecture.md) | the system at rest, the trace bus, life of a question |
| [Extensibility](docs/guides/extensibility.md) | add an adapter, add a layer, re-skin into a new project |
| [Stack matrix](docs/reference/stack-matrix.md) | per-layer trade-offs, defaults, switch triggers |
| [Ralph runbook](docs/runbooks/ralph-army.md) | the autonomous build harness |

## Status

Built and verified offline: 62 tests, `mypy` + `ruff` clean on the zero-dep profile.
Real-backend round-trips (cloud keys, Qdrant service) and the knowledge-graph retriever are the
open edges — the contracts for both are already frozen.

MIT licensed.
