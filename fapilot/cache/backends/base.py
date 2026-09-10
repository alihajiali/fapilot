from __future__ import annotations

import inspect
import math
import pickle
from collections.abc import Callable, Iterable, Mapping
from importlib import import_module
from typing import Any

DEFAULT_TIMEOUT = object()
_MISSING = object()


def default_key_function(key: str, key_prefix: str, version: int) -> str:
    return f"{key_prefix}:{version}:{key}"


def import_callable(path: str) -> Callable:
    module, _, name = path.rpartition(".")
    if not module:
        raise ValueError("Cache import paths must be fully qualified")
    return getattr(import_module(module), name)


def serialize(value: Any) -> bytes:
    # Numeric storage allows Redis/Memcached to implement atomic counters.
    return (
        str(value).encode() if type(value) is int else pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
    )


def deserialize(value: bytes) -> Any:
    try:
        return int(value)
    except ValueError:
        return pickle.loads(value)


class BaseCache:
    """Async cache contract. Custom backends implement the raw storage methods."""

    def __init__(self, location: str | list[str], params: dict[str, Any]) -> None:
        self.location = location
        self.default_timeout = params.get("TIMEOUT", 300)
        self.key_prefix = params.get("KEY_PREFIX", "")
        self.version = params.get("VERSION", 1)
        self.options = params.get("OPTIONS", {})
        function = params.get("KEY_FUNCTION") or default_key_function
        self.key_function = import_callable(function) if isinstance(function, str) else function

    def make_key(self, key: str, version: int | None = None) -> str:
        result = self.key_function(
            str(key), self.key_prefix, self.version if version is None else version
        )
        if not isinstance(result, str):
            raise TypeError("Cache KEY_FUNCTION must return a string")
        return result

    def get_timeout(self, timeout: Any = DEFAULT_TIMEOUT) -> float | None:
        value = self.default_timeout if timeout is DEFAULT_TIMEOUT else timeout
        result = None if value is None else float(value)
        if result is not None and not math.isfinite(result):
            raise ValueError("Cache timeout must be finite or None")
        return result

    async def get(self, key: str, default: Any = None, *, version: int | None = None) -> Any:
        value = await self._get(self.make_key(key, version))
        return default if value is None else deserialize(value)

    async def set(
        self, key: str, value: Any, timeout: Any = DEFAULT_TIMEOUT, *, version: int | None = None
    ) -> bool:
        return await self._set(
            self.make_key(key, version), serialize(value), self.get_timeout(timeout)
        )

    async def add(
        self, key: str, value: Any, timeout: Any = DEFAULT_TIMEOUT, *, version: int | None = None
    ) -> bool:
        return await self._add(
            self.make_key(key, version), serialize(value), self.get_timeout(timeout)
        )

    async def delete(self, key: str, *, version: int | None = None) -> bool:
        return await self._delete(self.make_key(key, version))

    async def touch(
        self, key: str, timeout: Any = DEFAULT_TIMEOUT, *, version: int | None = None
    ) -> bool:
        return await self._touch(self.make_key(key, version), self.get_timeout(timeout))

    async def has_key(self, key: str, *, version: int | None = None) -> bool:
        return await self._get(self.make_key(key, version)) is not None

    async def get_many(self, keys: Iterable[str], *, version: int | None = None) -> dict[str, Any]:
        result = {}
        for key in keys:
            value = await self.get(key, _MISSING, version=version)
            if value is not _MISSING:
                result[key] = value
        return result

    async def set_many(
        self, data: Mapping[str, Any], timeout: Any = DEFAULT_TIMEOUT, *, version: int | None = None
    ) -> list[str]:
        failed = []
        for key, value in data.items():
            if not await self.set(key, value, timeout, version=version):
                failed.append(key)
        return failed

    async def delete_many(self, keys: Iterable[str], *, version: int | None = None) -> None:
        for key in keys:
            await self.delete(key, version=version)

    async def get_or_set(
        self, key: str, default: Any, timeout: Any = DEFAULT_TIMEOUT, *, version: int | None = None
    ) -> Any:
        value = await self.get(key, _MISSING, version=version)
        if value is not _MISSING:
            return value
        value = default() if callable(default) else default
        if inspect.isawaitable(value):
            value = await value
        await self.add(key, value, timeout, version=version)
        return await self.get(key, value, version=version)

    async def incr(self, key: str, delta: int = 1, *, version: int | None = None) -> int:
        if type(delta) is not int:
            raise ValueError("Cache counter delta must be an integer")
        return await self._incr(self.make_key(key, version), delta)

    async def decr(self, key: str, delta: int = 1, *, version: int | None = None) -> int:
        return await self.incr(key, -delta, version=version)

    async def incr_version(self, key: str, delta: int = 1, *, version: int | None = None) -> int:
        current = self.version if version is None else version
        value = await self.get(key, _MISSING, version=current)
        if value is _MISSING:
            raise ValueError("Cache key does not exist")
        new_version = current + delta
        if new_version != current:
            await self.set(key, value, version=new_version)
            await self.delete(key, version=current)
        return new_version

    async def decr_version(self, key: str, delta: int = 1, *, version: int | None = None) -> int:
        return await self.incr_version(key, -delta, version=version)

    async def close(self) -> None:
        pass

    async def _get(self, key: str) -> bytes | None:
        raise NotImplementedError

    async def _set(self, key: str, value: bytes, timeout: float | None) -> bool:
        raise NotImplementedError

    async def _add(self, key: str, value: bytes, timeout: float | None) -> bool:
        raise NotImplementedError

    async def _delete(self, key: str) -> bool:
        raise NotImplementedError

    async def _touch(self, key: str, timeout: float | None) -> bool:
        raise NotImplementedError

    async def _incr(self, key: str, delta: int) -> int:
        raise NotImplementedError

    async def clear(self) -> bool:
        raise NotImplementedError

    def __getattr__(self, name: str) -> Any:
        # Django's async method spellings are available as aliases.
        methods = {
            "get",
            "set",
            "add",
            "delete",
            "touch",
            "has_key",
            "get_many",
            "set_many",
            "delete_many",
            "get_or_set",
            "incr",
            "decr",
            "incr_version",
            "decr_version",
            "clear",
            "close",
        }
        if name.startswith("a") and name[1:] in methods:
            return getattr(self, name[1:])
        raise AttributeError(name)
