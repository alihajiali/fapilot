from __future__ import annotations

import inspect
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

Receiver = Callable[..., Awaitable[None] | None]


class SignalDispatcher:
    def __init__(self) -> None:
        self._receivers: dict[str, list[Receiver]] = defaultdict(list)

    def connect(self, signal: str, receiver: Receiver) -> None:
        self._receivers[signal].append(receiver)

    async def emit(self, signal: str, **payload: Any) -> None:
        for receiver in self._receivers.get(signal, []):
            result = receiver(**payload)
            if inspect.isawaitable(result):
                await result

