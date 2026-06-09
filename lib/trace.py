"""The one trace bus. Every component emits a TraceEvent here; the UI, the logs,
and the demo narrative all read the same stream.

Two sinks: an append-only JSONL file per run (post-hoc debugging, eval evidence)
and an in-memory ring buffer (last 500 events) the UI polls. The ring buffer is
written by component threads and read by the UI threadpool, so it lives in a deque
behind a lock.
"""

import json
import threading
import time
from collections import deque
from dataclasses import asdict
from pathlib import Path
from typing import Any

from lib.contracts import TraceEvent

_RING_MAX = 500


class TraceBus:
    def __init__(self, run_id: str, runs_dir: str = "runs") -> None:
        self.run_id = run_id
        self._ring: deque[TraceEvent] = deque(maxlen=_RING_MAX)
        self._lock = threading.Lock()
        self.path = Path(runs_dir) / f"{run_id}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, component: str, event: str, **payload: Any) -> TraceEvent:
        ev = TraceEvent(
            ts=time.time(),
            run_id=self.run_id,
            component=component,
            event=event,
            payload=payload,
        )
        with self._lock:
            self._ring.append(ev)
            with self.path.open("a") as fh:
                fh.write(json.dumps(asdict(ev)) + "\n")
        return ev

    def recent(self, *, component_prefix: str | None = None) -> list[TraceEvent]:
        with self._lock:
            events = list(self._ring)
        if component_prefix:
            events = [e for e in events if e.component.startswith(component_prefix)]
        return events
