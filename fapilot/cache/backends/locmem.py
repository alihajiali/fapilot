from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any

from fapilot.cache.backends.base import BaseCache, deserialize, serialize

_stores: dict[str, OrderedDict[str, tuple[float | None, bytes]]] = {}
_locks: dict[str, Any] = {}
_registry_lock = threading.Lock()


class LocMemCache(BaseCache):
    """Process-local, thread-safe LRU cache shared by LOCATION."""

    def __init__(self, location: str | list[str], params: dict[str, Any]) -> None:
        super().__init__(location, params)
        if not isinstance(location, str):
            raise ValueError("Local memory LOCATION must be a string")
        with _registry_lock:
            self._store = _stores.setdefault(location, OrderedDict())
            self._lock = _locks.setdefault(location, threading.RLock())
        self.max_entries = int(self.options.get("MAX_ENTRIES", 300))
        self.cull_frequency = int(self.options.get("CULL_FREQUENCY", 3))
        if self.max_entries < 1 or self.cull_frequency < 0:
            raise ValueError("Invalid cache capacity or cull frequency")

    def _read(self, key: str) -> bytes | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires, value = entry
        if expires is not None and expires <= time.time():
            self._store.pop(key, None)
            return None
        self._store.move_to_end(key)
        return value

    def _write(self, key: str, value: bytes, timeout: float | None) -> bool:
        if timeout is not None and timeout <= 0:
            self._store.pop(key, None)
            return True
        if key not in self._store and len(self._store) >= self.max_entries:
            if self.cull_frequency == 0:
                self._store.clear()
            else:
                for _ in range(max(1, len(self._store) // self.cull_frequency)):
                    self._store.popitem(last=False)
        expires = None if timeout is None else time.time() + timeout
        self._store[key] = (expires, value)
        self._store.move_to_end(key)
        return True

    async def _get(self, key: str) -> bytes | None:
        with self._lock:
            return self._read(key)

    async def _set(self, key: str, value: bytes, timeout: float | None) -> bool:
        with self._lock:
            return self._write(key, value, timeout)

    async def _add(self, key: str, value: bytes, timeout: float | None) -> bool:
        with self._lock:
            if self._read(key) is not None:
                return False
            return self._write(key, value, timeout)

    async def _delete(self, key: str) -> bool:
        with self._lock:
            return self._store.pop(key, None) is not None

    async def _touch(self, key: str, timeout: float | None) -> bool:
        with self._lock:
            value = self._read(key)
            return False if value is None else self._write(key, value, timeout)

    async def _incr(self, key: str, delta: int) -> int:
        with self._lock:
            value = self._read(key)
            if value is None:
                raise ValueError("Cache key does not exist")
            number = deserialize(value)
            if type(number) is not int:
                raise ValueError("Cache value must be an integer")
            result = number + delta
            self._store[key] = (self._store[key][0], serialize(result))
            return result

    async def clear(self) -> bool:
        with self._lock:
            self._store.clear()
        return True
