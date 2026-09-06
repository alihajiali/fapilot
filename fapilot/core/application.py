from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from importlib import import_module

from fastapi import FastAPI

from fapilot.apps import AppRegistry
from fapilot.conf import FapilotSettings, get_settings
from fapilot.db.tortoise import close_orm, init_orm
from fapilot.events.dispatcher import SignalDispatcher


class Fapilot:
    def __init__(self, settings: FapilotSettings | None = None) -> None:
        self.settings = settings or get_settings()
        self.registry = AppRegistry()
        self.events = SignalDispatcher()

    def setup(self) -> None:
        self.registry.populate(self.settings.INSTALLED_APPS)

    def create_fastapi(self) -> FastAPI:
        self.setup()

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[None]:
            app.state.fapilot = self
            await init_orm(self.settings, self.registry)
            await self.events.emit("startup", app=app)
            try:
                yield
            finally:
                await self.events.emit("shutdown", app=app)
                await close_orm()

        app = FastAPI(debug=self.settings.DEBUG, lifespan=lifespan)
        app.state.fapilot = self
        self._install_middleware(app)
        self._include_app_routers(app)
        return app

    def _install_middleware(self, app: FastAPI) -> None:
        for dotted_path in self.settings.MIDDLEWARE:
            factory = import_string(dotted_path)
            factory(app)

    def _include_app_routers(self, app: FastAPI) -> None:
        for app_config in self.registry.get_apps():
            router = app_config.router
            if router is None:
                try:
                    api_module = import_module(f"{app_config.name}.api")
                except ModuleNotFoundError:
                    continue
                router = getattr(api_module, "router", None)
            if router is not None:
                prefix = (
                    app_config.router_prefix
                    or f"{self.settings.API_PREFIX}/{app_config.app_label}"
                )
                app.include_router(router, prefix=prefix, tags=[app_config.app_label])


def import_string(dotted_path: str) -> Callable:
    module_path, _, attribute = dotted_path.rpartition(".")
    if not module_path:
        raise ImportError(f"{dotted_path!r} is not a dotted import path")
    module = import_module(module_path)
    return getattr(module, attribute)


def create_app(settings: FapilotSettings | None = None) -> FastAPI:
    return Fapilot(settings=settings).create_fastapi()
