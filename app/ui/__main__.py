"""Entrypoint: `python -m app.ui` (the container CMD). Wires the configured stack
into the dashboard and launches it. Defaults to extractive answers (no LLM key
needed); set up the configured LLM in a deployment to get synthesized answers.
"""

import os
import uuid

from config.settings import Settings
from lib.contracts import EvalRow
from lib.ingestion.pipeline import ingest
from lib.retriever import SimpleRetriever
from lib.trace import TraceBus

from app.eval.dataset import generate
from app.eval.evaluator import RagasEvaluator
from app.eval.runner import answer_rows
from app.guardrails.guard import DefaultGuardrail
from app.memory.buffer import BufferMemory
from app.orchestration.orchestrator import DefaultOrchestrator
from app.ui.app import build_app


def main() -> None:
    settings = Settings.load(os.getenv("CHASSIS_PROFILE"))
    embedder = settings.build("embedder")
    store = settings.build("vectorstore")
    bus = TraceBus(run_id=uuid.uuid4().hex[:8])
    orchestrator = DefaultOrchestrator(
        SimpleRetriever(embedder, store),
        BufferMemory(embedder, store, collection="memory"),
        DefaultGuardrail(),
        trace=bus,
        k=settings.layers.get("retrieval", {}).get("k", 5),
    )

    def eval_fn(corpus: str) -> list[EvalRow]:
        if not corpus or not os.path.isdir(corpus):
            return []
        ingest(corpus, embedder, store, trace=bus)
        return RagasEvaluator().run(answer_rows(orchestrator, generate(corpus, n=5)))

    variant = "dark" if os.getenv("CHASSIS_THEME", "").lower() == "dark" else "light"
    demo = build_app(orchestrator, bus, variant=variant, eval_fn=eval_fn)
    demo.launch(server_name="0.0.0.0", server_port=8000, share=False)


if __name__ == "__main__":
    main()
