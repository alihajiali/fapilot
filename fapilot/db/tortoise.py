from __future__ import annotations

from tortoise import Tortoise

from fapilot.apps import AppRegistry
from fapilot.conf import FapilotSettings


def build_tortoise_config(settings: FapilotSettings, registry: AppRegistry) -> dict:
    apps: dict[str, dict] = {
        "models": {"models": ["aerich.models"], "default_connection": "default"}
    }
    for app_config in registry.get_apps():
        models = [f"{app_config.name}.models"]
        models.extend(app_config.tortoise_models)
        apps[app_config.app_label] = {"models": models, "default_connection": "default"}
    return {"connections": {"default": settings.DATABASE_URL}, "apps": apps}


async def init_orm(settings: FapilotSettings, registry: AppRegistry) -> None:
    await Tortoise.init(config=build_tortoise_config(settings, registry))
    if settings.DEBUG:
        await Tortoise.generate_schemas(safe=True)


async def close_orm() -> None:
    await Tortoise.close_connections()

