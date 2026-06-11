"""Centralized tuning knobs: the foundational ints + strings that shape app
behavior, in one place instead of scattered default args. Profiles override the
constructor-shaped ones per stack (k, window, recall_k, dim, model); these are
the code-level defaults everything falls back to. No imports — safe for any
layer to depend on. Each comment cites where the knob is consumed.
"""

# retrieval
# chunks fetched per query — lib/retriever.py, app/orchestration/orchestrator.py + specialists.py
RETRIEVAL_K = 5
CHUNKS_COLLECTION = "chassis"        # the corpus vector collection — lib/retriever.py

# memory — all consumed by app/memory/buffer.py (BufferMemory)
MEMORY_WINDOW = 8                    # turns kept verbatim before folding into the summary
MEMORY_RECALL_K = 3                  # long-term hits recalled per query
MEMORY_COLLECTION = "memory"         # memory's own vector collection
SUMMARY_MAX_TOKENS = 200             # LLM budget for the running summary (_summarize)

# llm — chat() defaults in lib/llm/anthropic_llm.py, openai_llm.py, ollama_llm.py
LLM_TEMPERATURE = 0.0
LLM_MAX_TOKENS = 1024
OLLAMA_HOST = "http://localhost:11434"   # OLLAMA_HOST env fallback — lib/llm/ollama_llm.py

# tools
TOOL_LOOP_MAX_ITERS = 5              # tool rounds per query — app/orchestration/tools.py

# extractive fallbacks (no-LLM answers) — app/orchestration/specialists.py (answer_synthesis)
EXTRACTIVE_SNIPPET_CHARS = 200       # chars kept per snippet in a joined answer
EXTRACTIVE_MAX_SNIPPETS = 3          # snippets joined per synthesis answer

# eval
EVAL_SEED_N = 10                     # rows per seed set — app/eval/dataset.py (generate)
GROUND_TRUTH_CHARS = 200             # degenerate ground-truth length — app/eval/dataset.py
CONTEXT_MIN_OVERLAP = 0.1            # "relevant context" threshold — app/eval/metrics.py
JUDGE_MAX_TOKENS = 8                 # judge replies with one number — app/eval/evaluator.py

# embeddings
HASHING_DIM = 256                    # zero-dep vector size — lib/embeddings/hashing.py

# trace — both consumed by lib/trace.py (TraceBus)
TRACE_RING_MAX = 500                 # in-memory ring buffer size the UI polls
RUNS_DIR = "runs"                    # per-run JSONL sink directory

# ui — both consumed by app/ui/__main__.py (demo.launch)
UI_HOST = "0.0.0.0"
UI_PORT = 8000

# api — both consumed by app/api/__main__.py (uvicorn.run); 8001 so it coexists with the ui
API_HOST = "0.0.0.0"
API_PORT = 8001
