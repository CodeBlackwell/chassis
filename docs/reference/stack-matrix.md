# Stack Pro/Cons Matrix

Every layer has options behind one contract. **The default is the lowest-friction option that still demonstrates the concept. Switch only on a named trigger** — a specific signal (company preference, key/compute availability, time budget), never a vibe. Anything without a trigger stays on default.

Each table: **Option | Pros | Cons | Default? | Switch trigger**.

## Orchestration — contract: `Orchestrator`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Custom (router + specialists) | Full explainability, zero framework debugging, trace bus hooks everywhere | You write the loop; no graph viz out of the box | **Yes** | — |
| LangGraph | Built-in graph visualization, checkpointing, ecosystem | Framework debugging under a clock; opinionated state model | No | They want graph viz, or are a LangGraph shop |
| CrewAI | Fast role-based multi-agent setup | Less control over the exact loop and tracing | No | Role-based agents are the explicit ask |

## LLM provider — contract: `LLM`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Provided cloud key (Anthropic/OpenAI) | Best quality, no local compute, fast | Costs money; dies if the key dies | **Yes** | — |
| Ollama (local) | No key, fully offline, free | Needs local compute/RAM; lower ceiling; slower | No | No key available, or the cloud key dies mid-demo |
| Azure / Bedrock | Enterprise compliance, existing contracts | More setup, region/quirk handling | No | They name a specific managed cloud |

## Embeddings — contract: `Embedder`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| all-MiniLM-L6-v2 (384-dim) | Tiny, fast, offline, great default | Lower retrieval quality than larger models | **Yes** | — |
| bge-small-en-v1.5 (384-dim) | Better quality, **same dim as MiniLM (free swap)** | Larger download | No | Want more quality and download time is fine |
| OpenAI text-embedding-3-small (1536-dim) | Strong quality, no local compute | Costs money; **different dim — see coupling** | No | No local compute available |
| Hashing (feature-hash, any dim) | Zero deps, deterministic, no model/download | Lexical overlap only, no semantics | No | Tests / CI / offline smoke |

> Coupling: dim is frozen at ingest. MiniLM ↔ bge is a free swap (both 384). Switching to OpenAI (1536) after ingest requires a full re-ingest.

## Vector DB — contract: `VectorStore`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Qdrant | Production-grade, real ANN, scales independently, the "prod" story | Needs a running service (docker-compose) | **Yes** | — |
| Chroma (in-mem) | Zero services, runs in-process, trivial setup | Not the production story; memory-bound | No | Zero-service environment needed |
| FAISS (pure lib) | No service, fast, battle-tested | Lowest-level; you manage persistence/metadata | No | Zero-service and you want raw control |
| Memory (in-process) | Zero deps (no numpy), brute-force cosine | O(n) search, not persistent | No | Tests / CI / offline smoke |

> Coupling: this choice drives deployment. Qdrant → docker-compose. Chroma/FAISS → single Dockerfile or bare process.

## Retrieval — contract: `Retriever` (+ optional `GraphStore`)

Default retrieval is vector-only over the `VectorStore`. A knowledge-graph option adds structural recall (vector hit → graph-expand to connected nodes) behind the same `Retriever` contract, via a `HybridRetriever` and a new optional `GraphStore`. See [extensibility.md](../guides/extensibility.md) Move 2 — this is the one deliberate pre-build contract addition.

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Vector-only | Simplest, one store, fewest moving parts | Misses structural/relational context | **Yes** | — |
| Hybrid + SQLite/NetworkX graph | Connected-evidence recall, in-process, zero service, graceful-degrade to vector | Two stores to keep in sync; Python-side traversal | No | The corpus has real structure (code, entities, citations) worth traversing |
| Hybrid + Neo4j graph | Native multi-hop + vector index in one engine, scales | A service to run; deployment weight | No | >100k chunks, or genuine multi-hop queries |

> Coupling note: the graph backend follows the same service-vs-in-process split as the vector DB. SQLite/NetworkX stays bare; Neo4j needs a service.

## Memory — contract: `Memory`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| In-process buffer + vector recall | No extra service, covers short + long term, simple | Lost on restart (not persistent) | **Yes** | — |
| Redis-backed | Persistent, shared across processes | Another service to run | No | Persistence is explicitly asked for |
| Framework checkpointer | Integrates with the orchestration framework | Couples memory to that framework | No | Already committed to that framework |

## Guardrails — contract: `Guardrail`

The base ships a passthrough stub, not a policy — what to enforce is domain-specific. A project registers its own rail under `guardrail` and selects it in a profile; the orchestrator's block seam already honors a failing verdict.

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Passthrough stub | Zero policy baked in; the base stays domain-neutral | Enforces nothing until a project adds a rail | **Yes** | — |
| Project-specific rules (heuristics + judge) | Tailored to the domain's risks; transparent | You write and maintain them | No | The domain needs input/output enforcement |
| Guardrails AI | Off-the-shelf validators, declarative | Another dependency; less transparent | No | They want a named library |
| NeMo Guardrails | Declarative rails, enterprise pedigree | Heavier, more setup | No | Enterprise/declarative rails are the ask |

## LLM eval — contract: `Evaluator`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Custom RAGAS-style + judge | Shows you understand the metrics, not just the import; no extra dep | You implement faithfulness/relevance/precision | **Yes** | — |
| RAGAS (library) | Named, recognizable metrics; less code | Dependency; less control over scoring | No | They want named metrics and time allows |
| DeepEval | Test-style assertions, CI-friendly | Another framework to learn | No | Eval-as-tests is the explicit ask |

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
