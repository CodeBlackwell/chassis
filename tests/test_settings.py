import pytest
from config.settings import Settings


def test_load_default_profile():
    s = Settings.load("qdrant-local")
    assert s.profile == "qdrant-local"
    assert s.impl("llm") == "anthropic"
    assert s.impl("vectorstore") == "qdrant"


def test_config_strips_impl():
    s = Settings(profile="x", layers={"vectorstore": {"impl": "qdrant", "url": "u", "k": 1}})
    assert s.config("vectorstore") == {"url": "u", "k": 1}
    assert s.impl("vectorstore") == "qdrant"


def test_env_override_flips_impl(monkeypatch):
    monkeypatch.setenv("CHASSIS_LLM_IMPL", "ollama")
    s = Settings.load("qdrant-local")
    assert s.impl("llm") == "ollama"


def test_profile_env_var_selects_file(monkeypatch):
    monkeypatch.setenv("CHASSIS_PROFILE", "faiss-bare")
    s = Settings.load()
    assert s.profile == "faiss-bare"
    assert s.impl("vectorstore") == "faiss"
    assert s.impl("llm") == "ollama"


def test_unknown_profile_raises():
    with pytest.raises(FileNotFoundError):
        Settings.load("does-not-exist")


def test_app_layers_build_from_profile():
    s = Settings.load("memory")
    embedder = s.build("embedder")
    store = s.build("vectorstore")
    orchestrator = s.build(
        "orchestrator",
        retriever=s.build("retriever", embedder=embedder, store=store),
        memory=s.build("memory", embedder=embedder, store=store),
        guardrail=s.build("guardrail"),
        router=s.build("router"),
        llm=s.build("llm"),
    )
    assert orchestrator.handle("hello").route == "chitchat"


def test_impl_none_builds_to_none():
    s = Settings.load("memory")  # memory profile declares llm: {impl: none}
    assert s.build("llm") is None


def test_impl_none_is_env_overridable(monkeypatch):
    monkeypatch.setenv("CHASSIS_LLM_IMPL", "ollama")
    s = Settings.load("memory")
    assert s.impl("llm") == "ollama"


def test_llm_fast_alias_resolves():
    from lib.registry import build

    fast = build("llm_fast", "ollama", model="m")
    assert type(fast).__name__ == "OllamaLLM"
