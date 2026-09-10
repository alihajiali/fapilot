# Events, background tasks, and realtime

[Documentation index](index.md)

## Signals

```python
from fapilot.events import SignalDispatcher

events = SignalDispatcher()


async def record_order(order_id: int):
    print(f"Recorded order {order_id}")


events.connect("order.created", record_order)
# In an async function: await events.emit("order.created", order_id=123)
```

`connect(signal, receiver)` appends a receiver. `emit(signal, **payload)` calls receivers
in registration order and awaits awaitable results. Synchronous receivers are also
supported and run on the event loop thread. An unknown signal is a no-op; duplicate
registration causes duplicate calls. Receiver exceptions propagate and stop delivery
to later receivers. There is no disconnect API, persistence, or cross-process transport.

Every `Fapilot` instance owns a dispatcher at `app.state.fapilot.events`. Its built-in
signals are `startup` and `shutdown`, each with `app` as a keyword argument. Use that
same dispatcher for application events if you want shared receivers; creating a new
`SignalDispatcher` creates an independent event bus. See [lifecycle](applications.md).

## Background tasks

```python
import asyncio
from fapilot.background import TaskQueue

queue = TaskQueue()


async def refresh_cache(key: str):
    await asyncio.sleep(0)
    return key


async def run_refresh():
    task = queue.spawn(refresh_cache, "catalog")
    return await task
```

`spawn` calls `asyncio.create_task` and returns the task. It requires a running event
loop and a callable returning a coroutine. Retain the returned task and handle results,
exceptions, cancellation, and shutdown according to your application needs. `TaskQueue`
is not a worker service: no retries, durable storage, scheduler, concurrency limit,
or automatic draining is provided. Work is lost if the process exits.

## Server-sent events

Add to a registered app's `api.py`:

```python
import asyncio
from fastapi import APIRouter, Request
from fapilot.realtime import EventSourceResponse, sse_event

router = APIRouter()


@router.get("/events")
async def events(request: Request):
    async def stream():
        for index in range(3):
            if await request.is_disconnected():
                break
            yield sse_event({"count": index}, event="tick", event_id=str(index))
            await asyncio.sleep(1)

    return EventSourceResponse(stream())
```

For app label `notifications`, try
`curl -N http://127.0.0.1:8000/api/notifications/events`.
`sse_event` JSON-encodes nonstring data, formats multiline data with repeated `data:`
lines, and adds optional `id:` and `event:` fields. The response is a streaming response
with `text/event-stream` media type. The helper does not implement heartbeats, replay,
retry fields, authentication, cache headers, or automatic disconnect handling.
Use server-controlled event names/IDs without newlines. Empty string data currently
produces no `data:` line. Configure reverse proxies to allow unbuffered streaming.

## WebSockets

Add to a registered app's `api.py`:

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fapilot.realtime import WebSocketHub

router = APIRouter()
hub = WebSocketHub()


@router.websocket("/ws")
async def chat(websocket: WebSocket):
    await hub.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            await hub.broadcast_text(message)
    except WebSocketDisconnect:
        pass
    finally:
        hub.disconnect(websocket)
```

For label `chat`, the URL is `ws://127.0.0.1:8000/api/chat/ws`.
`connect` accepts the socket and stores it. `disconnect` removes it without closing
it. `broadcast_text` sends sequentially to all stored sockets and removes sockets
whose send raises `RuntimeError`. Other exceptions propagate. Slow connections can
slow broadcasting. The hub has no rooms, authentication, message validation, or
cross-worker sharing; implement those as needed. Each worker has a separate hub.
