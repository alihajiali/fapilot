from __future__ import annotations

import asyncio
import hashlib
import os
import pickle
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from fapilot.cache.backends.base import BaseCache, deserialize, serialize

_locks: dict[str, Any] = {}
_registry_lock = threading.Lock()


class FileBasedCache(BaseCache):
    """Atomic file replacement, with blocking I/O moved off the event loop."""

    def __init__(self, location: str | list[str], params: dict[str, Any]) -> None:
        super().__init__(location, params)
        if not isinstance(location, str) or not location:
            raise ValueError("Filesystem cache requires a directory LOCATION")
        self.directory = Path(location).resolve()
        with _registry_lock:
            self._lock = _locks.setdefault(str(self.directory), threading.RLock())
        self.max_entries = int(self.options.get("MAX_ENTRIES", 300))
        self.cull_frequency = int(self.options.get("CULL_FREQUENCY", 3))
        if self.max_entries < 1 or self.cull_frequency < 0:
            raise ValueError("Invalid cache capacity or cull frequency")

    def _path(self, key: str) -> Path:
        return self.directory / (hashlib.sha256(key.encode()).hexdigest() + ".cache")

    def _read(self, path: Path) -> tuple[float | None, bytes] | None:
        try:
            with path.open("rb") as stream:
                expires, value = pickle.load(stream)
            if expires is not None and expires <= time.time():
                path.unlink(missing_ok=True)
                return None
            return expires, value
        except (FileNotFoundError, EOFError, pickle.UnpicklingError):
            return None

    def _write(self, path: Path, expires: float | None, value: bytes) -> None:
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        entries = list(self.directory.glob("*.cache"))
        if not path.exists() and len(entries) >= self.max_entries:
            count = (
                len(entries)
                if self.cull_frequency == 0
                else max(1, len(entries) // self.cull_frequency)
            )
            for entry in entries[:count]:
                entry.unlink(missing_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=self.directory)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                pickle.dump((expires, value), stream, pickle.HIGHEST_PROTOCOL)
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def _operate(self, action: str, key: str = "", value: Any = None, timeout=None) -> Any:
        with self._lock:
            path = self._path(key)
            if action == "clear":
                for entry in self.directory.glob("*.cache"):
                    entry.unlink(missing_ok=True)
                return True
            entry = self._read(path)
            if action == "get":
                return None if entry is None else entry[1]
            if action == "delete":
                path.unlink(missing_ok=True)
                return entry is not None
            if action == "incr":
                if entry is None:
                    raise ValueError("Cache key does not exist")
                number = deserialize(entry[1])
                if type(number) is not int:
                    raise ValueError("Cache value must be an integer")
                self._write(path, entry[0], serialize(number + value))
                return number + value
            if action == "add" and entry is not None:
                return False
            if action == "touch":
                if entry is None:
                    return False
                value = entry[1]
            if timeout is not None and timeout <= 0:
                path.unlink(missing_ok=True)
            else:
                expires = None if timeout is None else time.time() + timeout
                self._write(path, expires, value)
            return True

    async def _get(self, key: str) -> bytes | None:
        return await asyncio.to_thread(self._operate, "get", key)

    async def _set(self, key: str, value: bytes, timeout: float | None) -> bool:
        return await asyncio.to_thread(self._operate, "set", key, value, timeout)

    async def _add(self, key: str, value: bytes, timeout: float | None) -> bool:
        return await asyncio.to_thread(self._operate, "add", key, value, timeout)

    async def _delete(self, key: str) -> bool:
        return await asyncio.to_thread(self._operate, "delete", key)

    async def _touch(self, key: str, timeout: float | None) -> bool:
        return await asyncio.to_thread(self._operate, "touch", key, None, timeout)

    async def _incr(self, key: str, delta: int) -> int:
        return await asyncio.to_thread(self._operate, "incr", key, delta)

    async def clear(self) -> bool:
        return await asyncio.to_thread(self._operate, "clear")
