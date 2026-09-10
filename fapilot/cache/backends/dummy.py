from __future__ import annotations

from fapilot.cache.backends.base import BaseCache


class DummyCache(BaseCache):
    async def _get(self, key: str) -> bytes | None:
        return None

    async def _set(self, key: str, value: bytes, timeout: float | None) -> bool:
        return True

    async def _add(self, key: str, value: bytes, timeout: float | None) -> bool:
        return True

    async def _delete(self, key: str) -> bool:
        return False

    async def _touch(self, key: str, timeout: float | None) -> bool:
        return False

    async def _incr(self, key: str, delta: int) -> int:
        raise ValueError("Cache key does not exist")

    async def clear(self) -> bool:
        return True
