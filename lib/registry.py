"""Config-driven factory: a (layer, name) pair resolves to a concrete adapter.

Nothing imports a concrete adapter directly. Code depends on the contract in
lib.contracts; the registry resolves the class from config at startup via lazy
import. Referencing an adapter that isn't written yet is fine until something
actually calls build() for it.
"""

import importlib
from typing import Any

REGISTRY: dict[str, dict[str, str]] = {
    "llm": {
        "openai": "lib.llm.openai_llm:OpenAILLM",
        "anthropic": "lib.llm.anthropic_llm:AnthropicLLM",
        "ollama": "lib.llm.ollama_llm:OllamaLLM",
    },
    "embedder": {
        "minilm": "lib.embeddings.sbert:SbertEmbedder",  # model name via kwargs
        "bge": "lib.embeddings.sbert:SbertEmbedder",
        "openai": "lib.embeddings.openai_emb:OpenAIEmbedder",
    },
    "vectorstore": {
        "qdrant": "lib.vectorstore.qdrant_store:QdrantStore",
        "chroma": "lib.vectorstore.chroma_store:ChromaStore",
        "faiss": "lib.vectorstore.faiss_store:FaissStore",
    },
    "graphstore": {
        "sqlite": "lib.graphstore.sqlite_store:SqliteGraphStore",
        "neo4j": "lib.graphstore.neo4j_store:Neo4jGraphStore",
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
