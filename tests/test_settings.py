import pytest
from config.settings import Settings


def test_load_default_profile():
    s = Settings.load("qdrant-local")
    assert s.profile == "qdrant-local"
    assert s.impl("llm") == "anthropic"
    assert s.impl("vectorstore") == "qdrant"


def test_config_strips_impl():
    s = Settings.load("qdrant-local")
    cfg = s.config("vectorstore")
    assert "impl" not in cfg
    assert cfg["url"] == "http://localhost:6333"


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
