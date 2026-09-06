from __future__ import annotations

import json
from collections.abc import AsyncIterable
from typing import Any

from starlette.responses import StreamingResponse


def sse_event(data: Any, *, event: str | None = None, event_id: str | None = None) -> str:
    lines: list[str] = []
    if event_id:
        lines.append(f"id: {event_id}")
    if event:
        lines.append(f"event: {event}")
    payload = data if isinstance(data, str) else json.dumps(data)
    for line in payload.splitlines():
        lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"


class EventSourceResponse(StreamingResponse):
    def __init__(self, content: AsyncIterable[str]) -> None:
        super().__init__(content, media_type="text/event-stream")

