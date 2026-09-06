from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any


class TaskQueue:
    def spawn(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> asyncio.Task:
        return asyncio.create_task(func(*args, **kwargs))
