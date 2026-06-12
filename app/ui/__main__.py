"""Entrypoint: `python -m app.ui` (the container CMD). Builds the whole stack —
lib and app layers alike — from the active profile via the registry, then launches
the dashboard. Defaults to extractive answers (no LLM key needed). Loading data
into the store is the project's job (see docs/reference/stack-matrix.md,
Ingestion); wire an `eval_fn` into `build_app` to activate the Eval tab.
"""

import os
import uuid

from config import defaults
from config.settings import Settings
from lib.trace import TraceBus

from app.ui.app import build_app


def main() -> None:
    settings = Settings.load(os.getenv("CHASSIS_PROFILE"))
    embedder = settings.build("embedder")
    store = settings.build("vectorstore")
    llm = settings.build("llm")
    # fast tier (judge/summary roles) falls back to the primary model when unset
    llm_fast = settings.build("llm_fast") if "llm_fast" in settings.layers else llm
    bus = TraceBus(run_id=uuid.uuid4().hex[:8])
    orchestrator = settings.build(
        "orchestrator",
        retriever=settings.build("retriever", embedder=embedder, store=store),
        memory=settings.build("memory", embedder=embedder, store=store, llm=llm_fast),
        guardrail=settings.build("guardrail"),
        llm=llm,
        router=settings.build("router"),
        trace=bus,
    )

    variant = "dark" if os.getenv("CHASSIS_THEME", "").lower() == "dark" else "light"
    demo = build_app(orchestrator, bus, variant=variant)
    demo.launch(server_name=defaults.UI_HOST, server_port=defaults.UI_PORT, share=False)


if __name__ == "__main__":
    main()
