from __future__ import annotations

from typing import Any

from fapilot.cache.backends.base import BaseCache, import_callable
from fapilot.conf import FapilotSettings, get_settings


class CacheHandler:
    """Lazy backend instances scoped to one application or an explicit settings object."""

    def __init__(self, settings: FapilotSettings | None = None) -> None:
        self.settings = settings
        self._backends: dict[str, BaseCache] = {}

    def __getitem__(self, alias: str) -> BaseCache:
        if alias not in self._backends:
            settings = self.settings or get_settings()
            if alias not in settings.CACHES:
                raise KeyError(f"Unknown cache alias: {alias}")
            config = settings.CACHES[alias]
            factory = self._backend_class(config.BACKEND)
            instance = factory(config.LOCATION, config.model_dump())
            if not isinstance(instance, BaseCache):
                raise TypeError(
                    "Cache backends must subclass fapilot.cache.backends.base.BaseCache"
                )
            self._backends[alias] = instance
        return self._backends[alias]

    @staticmethod
    def _backend_class(path: str) -> type[BaseCache]:
        prefix = "django.core.cache.backends."
        if path.startswith(prefix):
            path = "fapilot.cache.backends." + path[len(prefix) :]
        factory = import_callable(path)
        if not isinstance(factory, type) or not issubclass(factory, BaseCache):
            raise TypeError("Cache backends must subclass BaseCache")
        return factory

    async def close_all(self) -> None:
        backends, self._backends = self._backends, {}
        errors = []
        for backend in backends.values():
            try:
                await backend.close()
            except Exception as error:
                errors.append(error)
        if errors:
            raise ExceptionGroup("Cache cleanup failed", errors)

    async def create_tables(self, alias: str | None = None) -> None:
        from fapilot.cache.backends.db import DatabaseCache

        settings = self.settings or get_settings()
        aliases = [alias] if alias else list(settings.CACHES)
        for name in aliases:
            config = settings.CACHES[name]
            if not issubclass(self._backend_class(config.BACKEND), DatabaseCache):
                if alias:
                    raise ValueError("Selected cache is not a database backend")
                continue
            backend = self[name]
            if not isinstance(backend, DatabaseCache):
                raise TypeError("Selected cache is not a DatabaseCache")
            await backend.create_table()


class DefaultCacheProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(caches["default"], name)


caches = CacheHandler()
cache = DefaultCacheProxy()
