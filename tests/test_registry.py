import pytest
from lib import registry


def test_unknown_layer_raises():
    with pytest.raises(KeyError):
        registry.build("nope", "whatever")


def test_unknown_name_raises():
    with pytest.raises(KeyError):
        registry.build("llm", "nonexistent")


def test_build_resolves_and_instantiates(monkeypatch):
    # Point a temp entry at a stdlib class to prove the factory end-to-end
    # without depending on adapters that aren't written yet.
    monkeypatch.setitem(
        registry.REGISTRY, "test", {"ordered": "collections:OrderedDict"}
    )
    obj = registry.build("test", "ordered")
    from collections import OrderedDict

    assert isinstance(obj, OrderedDict)


def test_build_passes_kwargs(monkeypatch):
    monkeypatch.setitem(
        registry.REGISTRY, "test", {"counter": "collections:Counter"}
    )
    obj = registry.build("test", "counter", a=2, b=3)
    assert obj["a"] == 2 and obj["b"] == 3
