"""Entrypoint: `python -m app.ui` (the container CMD). Builds the whole stack —
lib and app layers alike — from the active profile via the registry, then launches
the dashboard. Defaults to extractive answers (no LLM key needed); set up the
configured LLM in a deployment to get synthesized answers.
"""

import os
import uuid

from config.settings import Settings
from lib.contracts import EvalRow
from lib.ingestion.pipeline import ingest
from lib.trace import TraceBus

from app.eval.dataset import generate
from app.eval.runner import answer_rows
from app.ui.app import build_app


def main() -> None:
    settings = Settings.load(os.getenv("CHASSIS_PROFILE"))
    embedder = settings.build("embedder")
    store = settings.build("vectorstore")
    bus = TraceBus(run_id=uuid.uuid4().hex[:8])
    orchestrator = settings.build(
        "orchestrator",
        retriever=settings.build("retriever", embedder=embedder, store=store),
        memory=settings.build("memory", embedder=embedder, store=store),
        guardrail=settings.build("guardrail"),
        trace=bus,
    )
    evaluator = settings.build("evaluator")

    def eval_fn(corpus: str) -> list[EvalRow]:
        if not corpus or not os.path.isdir(corpus):
            return []
        ingest(corpus, embedder, store, trace=bus)
        return evaluator.run(answer_rows(orchestrator, generate(corpus, n=5)))

    variant = "dark" if os.getenv("CHASSIS_THEME", "").lower() == "dark" else "light"
    demo = build_app(orchestrator, bus, variant=variant, eval_fn=eval_fn)
    demo.launch(server_name="0.0.0.0", server_port=8000, share=False)


if __name__ == "__main__":
    main()
