import pytest

from fapilot.apps import AppConfig, AppRegistry
from fapilot.conf import FapilotSettings
from fapilot.conf.settings import DatabaseAppSettings
from fapilot.db.tortoise import build_tortoise_config


class UsersConfig(AppConfig):
    def __init__(self) -> None:
        super().__init__(name="apps.users", label="users")


def test_tortoise_config_includes_aerich_models_and_installed_apps() -> None:
    registry = AppRegistry()
    registry.populate(["tests.test_database.UsersConfig"])
    settings = FapilotSettings(DATABASE_URL="sqlite://:memory:")

    config = build_tortoise_config(settings, registry)

    assert config["connections"]["default"] == "sqlite://:memory:"
    assert "aerich.models" in config["apps"]["models"]["models"]
    assert config["apps"]["users"]["models"] == ["apps.users.models"]



def test_named_connections_route_installed_and_explicit_groups() -> None:
    registry = AppRegistry()
    registry.populate(["tests.test_database.UsersConfig"])
    settings = FapilotSettings(
        DATABASE_URL="sqlite://legacy.sqlite3",
        DATABASES={"default": "sqlite://primary.sqlite3", "analytics": "sqlite://stats.sqlite3"},
        DATABASE_APPS={
            "users": DatabaseAppSettings(default_connection="analytics"),
            "reports": DatabaseAppSettings(models=["reports.models", "metrics.models"]),
        },
    )
    config = build_tortoise_config(settings, registry)
    assert config["connections"]["default"] == "sqlite://primary.sqlite3"
    assert config["apps"]["users"] == {
        "models": ["apps.users.models"], "default_connection": "analytics"
    }
    assert config["apps"]["reports"]["models"] == ["reports.models", "metrics.models"]
    assert config["apps"]["reports"]["default_connection"] == "default"
    assert settings.DATABASE_APPS["users"].models is None


@pytest.mark.parametrize("groups, message", [
    ({"users": {"default_connection": "missing"}}, "unknown connection"),
    ({"unknown": {}}, "explicit model modules"),
    ({"users": {"models": []}}, "nonempty model modules"),
    ({"users": {"models": [" "]}}, "nonempty model modules"),
    ({"models": {"models": ["other.models"]}}, "reserved"),
    ({"reports": {"models": ["apps.users.models"]}}, "multiple database apps"),
])
def test_invalid_database_mapping(groups, message) -> None:
    registry = AppRegistry()
    registry.populate(["tests.test_database.UsersConfig"])
    with pytest.raises(ValueError, match=message):
        build_tortoise_config(FapilotSettings(DATABASE_APPS=groups), registry)


def test_models_are_written_to_their_mapped_database(tmp_path, monkeypatch) -> None:
    import asyncio
    import sqlite3
    import sys
    import types

    from tortoise import fields
    from tortoise.models import Model

    from fapilot.db.tortoise import close_orm, init_orm

    class Account(Model):
        id = fields.IntField(primary_key=True)
        name = fields.CharField(max_length=50)

    class Report(Model):
        id = fields.IntField(primary_key=True)
        title = fields.CharField(max_length=50)

    for name, model in [("test_primary_models", Account), ("test_report_models", Report)]:
        module = types.ModuleType(name)
        module.__dict__["__models__"] = [model]
        monkeypatch.setitem(sys.modules, name, module)
    primary = tmp_path / "primary.sqlite3"
    analytics = tmp_path / "analytics.sqlite3"
    settings = FapilotSettings(
        DEBUG=True,
        DATABASES={"default": f"sqlite://{primary}", "analytics": f"sqlite://{analytics}"},
        DATABASE_APPS={
            "accounts": DatabaseAppSettings(models=["test_primary_models"]),
            "reports": DatabaseAppSettings(
                models=["test_report_models"], default_connection="analytics"
            ),
        },
    )

    async def exercise():
        try:
            await init_orm(settings, AppRegistry())
            await Account.create(name="Alice")
            await Report.create(title="Monthly report")
            assert await Account.all().count() == 1
            assert await Report.all().count() == 1
        finally:
            await close_orm()

    asyncio.run(exercise())
    with sqlite3.connect(primary) as connection:
        assert connection.execute("SELECT name FROM account").fetchall() == [("Alice",)]
        assert not connection.execute(
            "SELECT name FROM sqlite_master WHERE name = 'report'"
        ).fetchall()
    with sqlite3.connect(analytics) as connection:
        assert connection.execute("SELECT title FROM report").fetchall() == [("Monthly report",)]
        assert not connection.execute(
            "SELECT name FROM sqlite_master WHERE name = 'account'"
        ).fetchall()


def test_http_requests_can_use_lifespan_database(tmp_path, monkeypatch) -> None:
    import sys
    import types

    from fastapi.testclient import TestClient
    from tortoise import fields
    from tortoise.models import Model

    from fapilot import create_app

    class Entry(Model):
        id = fields.IntField(primary_key=True)
        name = fields.CharField(max_length=50)

    module = types.ModuleType("test_http_models")
    module.__dict__["__models__"] = [Entry]
    monkeypatch.setitem(sys.modules, "test_http_models", module)
    app = create_app(FapilotSettings(
        DEBUG=True,
        DATABASE_URL=f"sqlite://{tmp_path / 'http.sqlite3'}",
        DATABASES={},
        DATABASE_APPS={"entries": DatabaseAppSettings(models=["test_http_models"])},
        INSTALLED_APPS=[],
        MIDDLEWARE=[],
    ))

    @app.post("/entries")
    async def create_entry():
        entry = await Entry.create(name="Created through HTTP")
        return {"id": entry.id, "name": entry.name}

    with TestClient(app) as client:
        response = client.post("/entries")
        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "Created through HTTP"}
