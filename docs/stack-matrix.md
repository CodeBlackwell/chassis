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

> Coupling: dim is frozen at ingest. MiniLM ↔ bge is a free swap (both 384). Switching to OpenAI (1536) after ingest requires a full re-ingest.

## Vector DB — contract: `VectorStore`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Qdrant | Production-grade, real ANN, scales independently, the "prod" story | Needs a running service (docker-compose) | **Yes** | — |
| Chroma (in-mem) | Zero services, runs in-process, trivial setup | Not the production story; memory-bound | No | Zero-service environment needed |
| FAISS (pure lib) | No service, fast, battle-tested | Lowest-level; you manage persistence/metadata | No | Zero-service and you want raw control |

> Coupling: this choice drives deployment. Qdrant → docker-compose. Chroma/FAISS → single Dockerfile or bare process.

## Memory — contract: `Memory`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| In-process buffer + vector recall | No extra service, covers short + long term, simple | Lost on restart (not persistent) | **Yes** | — |
| Redis-backed | Persistent, shared across processes | Another service to run | No | Persistence is explicitly asked for |
| Framework checkpointer | Integrates with the orchestration framework | Couples memory to that framework | No | Already committed to that framework |

## Guardrails — contract: `Guardrail`

| Option | Pros | Cons | Default? | Switch trigger |
|--------|------|------|----------|----------------|
| Custom (Pydantic + heuristics + judge) | Named attack classes, transparent, fast, controllable | You maintain the heuristics | **Yes** | — |
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
