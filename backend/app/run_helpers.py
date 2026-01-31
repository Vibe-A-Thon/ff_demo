import asyncio
import json
from pathlib import Path
from typing import Any, Dict
from app.config import TRACE_ROOT
from app.db import db
from app.models import RunEvent

class EventBus:
    def __init__(self):
        self.active_queues: Dict[str, asyncio.Queue] = {}

    def get_queue(self, run_id: str) -> asyncio.Queue:
        if run_id not in self.active_queues:
            self.active_queues[run_id] = asyncio.Queue()
        return self.active_queues[run_id]

    async def publish(self, run_id: str, event: Dict[str, Any]):
        queue = self.active_queues.get(run_id)
        if queue:
            await queue.put(event)


event_bus = EventBus()


def append_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def get_trace_path(run_id: str) -> Path:
    return TRACE_ROOT / run_id / "trace.jsonl"


async def write_trace(run_id: str, entry: Dict[str, Any]) -> None:
    trace_path = get_trace_path(run_id)
    await asyncio.to_thread(append_line, trace_path, json.dumps(entry, default=str))


async def record_run_event(run_id: str, event_type: str, payload: Dict[str, Any]) -> RunEvent:
    event = RunEvent(run_id=run_id, event_type=event_type, payload=payload)
    await db.run_events.insert_one(event.model_dump())
    await event_bus.publish(run_id, event.model_dump())
    await write_trace(run_id, {"event_type": event_type, "payload": payload})
    return event
