from fapilot.conf.settings import FapilotSettings, load_settings


def test_settings_accept_django_style_uppercase_values() -> None:
    settings = FapilotSettings(
        DEBUG=True,
        SECRET_KEY="secret",
        INSTALLED_APPS=["tests.sample_app.apps.SampleConfig"],
    )

    assert settings.DEBUG is True
    assert settings.SECRET_KEY == "secret"
    assert settings.INSTALLED_APPS == ["tests.sample_app.apps.SampleConfig"]


def test_load_settings_without_module_uses_defaults() -> None:
    settings = load_settings(None)

    assert settings.API_PREFIX == "/api"
    assert settings.DEFAULT_PAGE_SIZE == 20

