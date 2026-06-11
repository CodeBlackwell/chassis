"""Thin HTTP layer over the Orchestrator contract — the same `handle(query) -> Answer`
seam the UI and eval consume, exposed as JSON. Handlers are sync (FastAPI runs them in
its threadpool, so the no-async mandate holds). Ships no auth, rate limiting, or CORS
policy — like guardrails, those are per-project policy on a wired seam.
"""

from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from pydantic import BaseModel

if TYPE_CHECKING:
    from lib.contracts import Orchestrator
    from lib.trace import TraceBus


class AskRequest(BaseModel):
    query: str


def create_app(orchestrator: "Orchestrator", bus: "TraceBus | None" = None) -> FastAPI:
    api = FastAPI(title="CHASSIS")

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post("/ask")
    def ask(req: AskRequest) -> dict[str, Any]:
        return asdict(orchestrator.handle(req.query))

    @api.get("/trace")
    def trace(component: str = "") -> list[dict[str, Any]]:
        events = bus.recent(component_prefix=component) if bus else []
        return [asdict(e) for e in events]

    return api
