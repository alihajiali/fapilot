from fapilot.apps import AppConfig, AppRegistry


class InlineConfig(AppConfig):
    def __init__(self) -> None:
        super().__init__(name="tests.test_registry", label="inline")


def test_registry_loads_app_config_by_dotted_path() -> None:
    registry = AppRegistry()

    registry.populate(["tests.test_registry.InlineConfig"])

    assert registry.ready is True
    assert registry.get_app("inline").name == "tests.test_registry"

