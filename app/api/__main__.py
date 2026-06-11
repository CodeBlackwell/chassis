"""Entrypoint: `python -m app.api`. Builds the whole stack from the active profile
via the registry — the same assembly as the dashboard — then serves it over HTTP.
Loading data into the store is the project's job (see docs/reference/stack-matrix.md,
Ingestion).
"""

import os
import uuid

import uvicorn
from config import defaults
from config.settings import Settings
from lib.trace import TraceBus

from app.api.app import create_app


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
    uvicorn.run(create_app(orchestrator, bus), host=defaults.API_HOST, port=defaults.API_PORT)


if __name__ == "__main__":
    main()
