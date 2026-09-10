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



def test_database_settings_from_environment(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASES", '{"analytics":"sqlite://analytics.sqlite3"}')
    monkeypatch.setenv("DATABASE_APPS", '{"reports":{"models":["reports.models"]}}')
    monkeypatch.setenv("DATABASE_APPS__reports__default_connection", "analytics")
    settings = FapilotSettings()
    assert settings.DATABASES == {"analytics": "sqlite://analytics.sqlite3"}
    assert settings.DATABASE_APPS["reports"].models == ["reports.models"]
    assert settings.DATABASE_APPS["reports"].default_connection == "analytics"
