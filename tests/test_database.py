from fapilot.apps import AppConfig, AppRegistry
from fapilot.conf import FapilotSettings
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

