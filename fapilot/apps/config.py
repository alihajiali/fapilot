from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter


@dataclass(slots=True)
class AppConfig:
    name: str
    label: str | None = None
    verbose_name: str | None = None
    router: APIRouter | None = None
    router_prefix: str | None = None
    tortoise_models: list[str] = field(default_factory=list)
    migrations_package: str | None = None

    def ready(self) -> None:
        """Hook called after every app is imported and registered."""

    @property
    def app_label(self) -> str:
        return self.label or self.name.rsplit(".", 1)[-1]

    def as_tortoise_app(self) -> dict[str, Any]:
        models = [*self.tortoise_models]
        if self.migrations_package is not None:
            models.append(self.migrations_package)
        return {"models": models, "default_connection": "default"}

