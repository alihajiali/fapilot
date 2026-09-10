from __future__ import annotations

import importlib
import os
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class JWTSettings(BaseSettings):
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    issuer: str = "fapilot"


class DatabaseAppSettings(BaseModel):
    """A model group and the named connection used for its queries and schema."""

    model_config = {"extra": "forbid"}
    default_connection: str = "default"
    models: list[str] | None = None


class FapilotSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=True,
    )

    DEBUG: bool = False
    SECRET_KEY: str = Field(default="change-me")
    ALLOWED_HOSTS: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])
    DATABASE_URL: str = "sqlite://db.sqlite3"
    DATABASES: dict[str, str] = Field(default_factory=dict)
    DATABASE_APPS: dict[str, DatabaseAppSettings] = Field(default_factory=dict)
    INSTALLED_APPS: list[str] = Field(default_factory=list)
    MIDDLEWARE: list[str] = Field(default_factory=list)
    CORS_ALLOWED_ORIGINS: list[str] = Field(default_factory=list)
    TIME_ZONE: str = "UTC"
    LANGUAGE_CODE: str = "en-us"
    API_PREFIX: str = "/api"
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    ADMIN_ENABLED: bool = False
    ADMIN_URL: str = "/admin"
    ADMIN_SITE: str = "fapilot.admin.site"
    ADMIN_MODULES: list[str] = Field(default_factory=list)
    ADMIN_SECURE_COOKIES: bool = True
    ADMIN_SESSION_SECONDS: int = Field(default=3600, ge=60, le=86400)
    AUTH_USER_MODEL: str = "users.User"
    JWT_SETTINGS: JWTSettings = Field(default_factory=JWTSettings)
    LOGGING: dict[str, Any] = Field(default_factory=dict)

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> Any:
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        return value


def load_settings(settings_module: str | None = None) -> FapilotSettings:
    module_name = settings_module or os.getenv("FAPILOT_SETTINGS_MODULE")
    if module_name is None:
        return FapilotSettings()
    module = importlib.import_module(module_name)
    values = {
        key: getattr(module, key)
        for key in dir(module)
        if key.isupper() and not key.startswith("_")
    }
    return FapilotSettings(**values)


@lru_cache
def get_settings() -> FapilotSettings:
    return load_settings()
