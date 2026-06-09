from config.settings import Settings
from lib import registry
from lib.contracts import Message
from lib.embeddings.sbert import SbertEmbedder
from lib.llm.anthropic_llm import AnthropicLLM
from lib.llm.ollama_llm import OllamaLLM, _payload


def test_registry_builds_ollama():
    obj = registry.build("llm", "ollama", model="llama3.1:8b")
    assert isinstance(obj, OllamaLLM)
    assert obj.model == "llama3.1:8b"


def test_registry_builds_anthropic_without_sdk_installed():
    # Lazy import: construction succeeds even if `anthropic` is absent.
    obj = registry.build("llm", "anthropic", model="claude-sonnet-4-6")
    assert isinstance(obj, AnthropicLLM)


def test_registry_builds_minilm_without_torch_installed():
    obj = registry.build("embedder", "minilm", model="sentence-transformers/all-MiniLM-L6-v2")
    assert isinstance(obj, SbertEmbedder)
    assert obj.model_name.endswith("all-MiniLM-L6-v2")


def test_settings_build_constructs_llm_from_profile():
    settings = Settings.load("faiss-bare")  # llm impl = ollama
    assert isinstance(settings.build("llm"), OllamaLLM)


def test_ollama_payload_shape():
    payload = _payload("m", [Message("user", "hi")], 0.2, 64)
    assert payload["model"] == "m"
    assert payload["stream"] is False
    assert payload["messages"] == [{"role": "user", "content": "hi"}]
    assert payload["options"] == {"temperature": 0.2, "num_predict": 64}
