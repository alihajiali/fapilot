from __future__ import annotations

from tortoise import Tortoise

from fapilot.apps import AppRegistry
from fapilot.conf import FapilotSettings


def build_tortoise_config(settings: FapilotSettings, registry: AppRegistry) -> dict:
    connections = {"default": settings.DATABASE_URL, **settings.DATABASES}
    for alias, url in connections.items():
        if not alias.strip() or not url.strip():
            raise ValueError("Database connection names and URLs must not be empty")

    apps: dict[str, dict] = {
        "models": {"models": ["aerich.models"], "default_connection": "default"}
    }
    for app_config in registry.get_apps():
        if app_config.app_label == "models":
            raise ValueError("App label 'models' is reserved for migration metadata")
        models = [f"{app_config.name}.models", *app_config.tortoise_models]
        apps[app_config.app_label] = {"models": models, "default_connection": "default"}

    for label, group in settings.DATABASE_APPS.items():
        if not label.strip() or label == "models":
            raise ValueError("Database app labels must be nonempty; 'models' is reserved")
        if group.default_connection not in connections:
            raise ValueError(f"Database app {label!r} references an unknown connection")
        if group.models is None:
            if label not in apps:
                raise ValueError(f"Database app {label!r} needs explicit model modules")
            models = apps[label]["models"]
        else:
            models = list(group.models)
        if not models or any(not module.strip() for module in models):
            raise ValueError(f"Database app {label!r} needs nonempty model modules")
        apps[label] = {"models": models, "default_connection": group.default_connection}

    owners: dict[str, str] = {}
    for label, app in apps.items():
        for module in app["models"]:
            if module in owners and owners[module] != label:
                raise ValueError(f"Model module {module!r} is assigned to multiple database apps")
            owners[module] = label
    return {"connections": connections, "apps": apps}


async def init_orm(settings: FapilotSettings, registry: AppRegistry) -> None:
    # ASGI requests run in tasks separate from the lifespan task.
    await Tortoise.init(
        config=build_tortoise_config(settings, registry), _enable_global_fallback=True
    )
    if settings.DEBUG:
        await Tortoise.generate_schemas(safe=True)


async def close_orm() -> None:
    await Tortoise.close_connections()

