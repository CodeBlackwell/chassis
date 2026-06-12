"""Config-driven factory: a (layer, name) pair resolves to a concrete adapter.

Nothing imports a concrete adapter directly. Code depends on the contract in
lib.contracts; the registry resolves the class from config at startup via lazy
import. Referencing an adapter that isn't written yet is fine until something
actually calls build() for it.
"""

import importlib
from typing import Any

_LLM_IMPLS = {
    "openai": "lib.llm.openai_llm:OpenAILLM",
    "anthropic": "lib.llm.anthropic_llm:AnthropicLLM",
    "ollama": "lib.llm.ollama_llm:OllamaLLM",
}

REGISTRY: dict[str, dict[str, str]] = {
    "llm": _LLM_IMPLS,
    "llm_fast": _LLM_IMPLS,  # second model slot (judge/summary tier); same impls
    "embedder": {
        "minilm": "lib.embeddings.sbert:SbertEmbedder",  # model name via kwargs
        "bge": "lib.embeddings.sbert:SbertEmbedder",
        "openai": "lib.embeddings.openai_emb:OpenAIEmbedder",
        "hashing": "lib.embeddings.hashing:HashingEmbedder",  # zero-dep, tests/CI
    },
    "vectorstore": {
        "qdrant": "lib.vectorstore.qdrant_store:QdrantStore",
        "chroma": "lib.vectorstore.chroma_store:ChromaStore",
        "faiss": "lib.vectorstore.faiss_store:FaissStore",
        "memory": "lib.vectorstore.memory_store:MemoryStore",  # zero-dep, tests/CI
    },
    "graphstore": {
        "sqlite": "lib.graphstore.sqlite_store:SqliteGraphStore",
        "neo4j": "lib.graphstore.neo4j_store:Neo4jGraphStore",
    },
    "router": {
        "keyword": "app.orchestration.router:KeywordRouter",
    },
    "retriever": {
        "simple": "lib.retriever:SimpleRetriever",
    },
    "memory": {
        "buffer": "app.memory.buffer:BufferMemory",
    },
    "guardrail": {
        "passthrough": "app.guardrails.guard:PassthroughGuardrail",
    },
    "orchestrator": {
        "default": "app.orchestration.orchestrator:DefaultOrchestrator",
    },
    "evaluator": {
        "ragas": "app.eval.evaluator:RagasEvaluator",
    },
}


def build(layer: str, name: str, **kwargs: Any) -> Any:
    try:
        target = REGISTRY[layer][name]
    except KeyError:
        raise KeyError(f"no adapter registered for {layer!r}/{name!r}") from None
    module_path, cls_name = target.split(":")
    module = importlib.import_module(module_path)
    return getattr(module, cls_name)(**kwargs)
