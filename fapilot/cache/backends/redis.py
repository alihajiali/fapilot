from __future__ import annotations

import math
import random
import re
from typing import Any

from fapilot.cache.backends.base import BaseCache


class RedisCache(BaseCache):
    def __init__(self, location: str | list[str], params: dict[str, Any]) -> None:
        super().__init__(location, params)
        try:
            from redis.asyncio import Redis
        except ImportError as error:
            raise ImportError("RedisCache requires: pip install 'fapilot[cache-redis]'") from error
        locations = re.split(r"[;,]", location) if isinstance(location, str) else location
        if not locations or any(not url.strip() for url in locations):
            raise ValueError("Redis cache requires at least one server URL")
        options = dict(self.options)
        if options.get("decode_responses"):
            raise ValueError("Redis cache requires decode_responses=False for serialized values")
        self._clients = [Redis.from_url(url.strip(), **options) for url in locations]

    @property
    def _writer(self) -> Any:
        return self._clients[0]

    async def _get(self, key: str) -> bytes | None:
        client = random.choice(self._clients[1:]) if len(self._clients) > 1 else self._writer
        return await client.get(key)

    async def _set(self, key: str, value: bytes, timeout: float | None) -> bool:
        if timeout is not None and timeout <= 0:
            await self._writer.delete(key)
            return True
        milliseconds = None if timeout is None else max(1, math.ceil(timeout * 1000))
        return bool(await self._writer.set(key, value, px=milliseconds))

    async def _add(self, key: str, value: bytes, timeout: float | None) -> bool:
        if timeout is not None and timeout <= 0:
            return not bool(await self._writer.exists(key))
        milliseconds = None if timeout is None else max(1, math.ceil(timeout * 1000))
        return bool(await self._writer.set(key, value, px=milliseconds, nx=True))

    async def _delete(self, key: str) -> bool:
        return bool(await self._writer.delete(key))

    async def _touch(self, key: str, timeout: float | None) -> bool:
        if timeout is None:
            return bool(
                await self._writer.eval(
                    "if redis.call('exists', KEYS[1]) == 0 then return 0 end "
                    "redis.call('persist', KEYS[1]); return 1",
                    1,
                    key,
                )
            )
        return bool(await self._writer.pexpire(key, math.ceil(timeout * 1000)))

    async def _incr(self, key: str, delta: int) -> int:
        from redis.exceptions import ResponseError

        try:
            result = await self._writer.eval(
                "if redis.call('exists', KEYS[1]) == 0 then return false end "
                "return redis.call('incrby', KEYS[1], ARGV[1])",
                1,
                key,
                delta,
            )
        except ResponseError as error:
            raise ValueError("Cache value must be an integer") from error
        if result is None:
            raise ValueError("Cache key does not exist")
        return int(result)

    async def clear(self) -> bool:
        await self._writer.flushdb()
        return True

    async def close(self) -> None:
        for client in self._clients:
            await client.aclose()
