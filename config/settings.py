"""Env-driven config. CHASSIS_PROFILE picks a profile yaml; per-layer
CHASSIS_<LAYER>_IMPL env vars override the impl. That override path is the
live-pivot mechanism: one env var flips a layer without editing a file.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

_PROFILES = Path(__file__).parent / "profiles"
_OVERRIDABLE = (
    "llm", "embedder", "vectorstore", "graphstore",
    "retriever", "memory", "guardrail", "orchestrator", "evaluator",
)


@dataclass
class Settings:
    profile: str
    layers: dict[str, dict[str, Any]] = field(default_factory=dict)

    def impl(self, layer: str) -> str:
        return str(self.layers[layer]["impl"])

    def config(self, layer: str) -> dict[str, Any]:
        return {k: v for k, v in self.layers[layer].items() if k != "impl"}

    def build(self, layer: str, **extra: Any) -> Any:
        # extra carries constructed dependencies (embedder=, store=, trace=...)
        # that profile YAML can't express
        from lib.registry import build

        return build(layer, self.impl(layer), **{**self.config(layer), **extra})

    @classmethod
    def load(cls, profile: str | None = None) -> "Settings":
        load_dotenv()
        if profile is None:
            profile = os.getenv("CHASSIS_PROFILE", "qdrant-local")
        path = _PROFILES / f"{profile}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"no profile {profile!r} at {path}")
        layers: dict[str, dict[str, Any]] = yaml.safe_load(path.read_text()) or {}
        for layer in _OVERRIDABLE:
            override = os.getenv(f"CHASSIS_{layer.upper()}_IMPL")
            if override and layer in layers:
                layers[layer]["impl"] = override
        return cls(profile=profile, layers=layers)
