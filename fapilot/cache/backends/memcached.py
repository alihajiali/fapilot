from __future__ import annotations

import asyncio
import math
import re
import threading
import time
from typing import Any

from fapilot.cache.backends.base import BaseCache


class _MemcachedCache(BaseCache):
    def __init__(self, location: str | list[str], params: dict[str, Any]) -> None:
        super().__init__(location, params)
        self._lock = threading.Lock()
        locations = re.split(r"[;,]", location) if isinstance(location, str) else location
        if not locations or any(not address.strip() for address in locations):
            raise ValueError("Memcached cache requires at least one server")
        self._servers = [address.strip() for address in locations]
        self._client: Any = None

    def make_key(self, key: str, version: int | None = None) -> str:
        result = super().make_key(key, version)
        if len(result.encode()) > 250 or any(
            ord(char) <= 32 or ord(char) == 127 for char in result
        ):
            raise ValueError(
                "Memcached keys must be <=250 bytes with no whitespace/control characters"
            )
        return result

    def _expiry(self, timeout: float | None) -> int:
        if timeout is None:
            return 0
        if timeout <= 0:
            return int(time.time()) - 1
        seconds = math.ceil(timeout)
        return seconds if seconds <= 2592000 else int(time.time()) + seconds

    def _call_sync(self, method: str, *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            return getattr(self._client, method)(*args, **kwargs)

    async def _call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self._call_sync, method, *args, **kwargs)

    async def _get(self, key: str) -> bytes | None:
        return await self._call("get", key)

    async def _set(self, key: str, value: bytes, timeout: float | None) -> bool:
        if timeout is not None and timeout <= 0:
            await self._delete(key)
            return True
        return bool(await self._call("set", key, value, **self._timeout_kwargs(timeout)))

    async def _add(self, key: str, value: bytes, timeout: float | None) -> bool:
        return bool(await self._call("add", key, value, **self._timeout_kwargs(timeout)))

    async def _delete(self, key: str) -> bool:
        return bool(await self._call("delete", key))

    async def _touch(self, key: str, timeout: float | None) -> bool:
        return bool(await self._call("touch", key, self._expiry(timeout)))

    async def _incr(self, key: str, delta: int) -> int:
        value = await self._call("incr" if delta >= 0 else "decr", key, abs(delta))
        if value is None:
            raise ValueError("Cache key does not exist")
        return int(value)

    async def clear(self) -> bool:
        await self._call("flush_all")
        return True

    def _timeout_kwargs(self, timeout: float | None) -> dict[str, int]:
        raise NotImplementedError


class PyMemcacheCache(_MemcachedCache):
    def __init__(self, location: str | list[str], params: dict[str, Any]) -> None:
        super().__init__(location, params)
        try:
            from pymemcache.client.hash import HashClient
        except ImportError as error:
            raise ImportError(
                "PyMemcacheCache requires: pip install 'fapilot[cache-pymemcache]'"
            ) from error
        servers = []
        for address in self._servers:
            if address.startswith("unix:"):
                servers.append(address[5:])
            else:
                host, separator, port = address.rpartition(":")
                if not separator:
                    host, port = address, "11211"
                servers.append((host.strip("[]"), int(port)))
        options = {"allow_unicode_keys": True, "default_noreply": False, **self.options}
        if options.get("default_noreply"):
            raise ValueError("Cache add/delete semantics require default_noreply=False")
        self._client = HashClient(servers, **options)

    def _timeout_kwargs(self, timeout: float | None) -> dict[str, int]:
        return {"expire": self._expiry(timeout)}

    async def close(self) -> None:
        await self._call("close")


class PyLibMCCache(_MemcachedCache):
    def __init__(self, location: str | list[str], params: dict[str, Any]) -> None:
        super().__init__(location, params)
        try:
            import pylibmc
        except ImportError as error:
            raise ImportError(
                "PyLibMCCache requires: pip install 'fapilot[cache-pylibmc]'"
            ) from error
        servers = [
            address[5:] if address.startswith("unix:") else address for address in self._servers
        ]
        self._client = pylibmc.Client(servers, **{"behaviors": {}, **self.options})
        self._not_found = vars(pylibmc)["NotFound"]

    def _timeout_kwargs(self, timeout: float | None) -> dict[str, int]:
        return {"time": self._expiry(timeout)}

    async def _incr(self, key: str, delta: int) -> int:
        try:
            return await super()._incr(key, delta)
        except self._not_found as error:
            raise ValueError("Cache key does not exist") from error

    async def close(self) -> None:
        await self._call("disconnect_all")
