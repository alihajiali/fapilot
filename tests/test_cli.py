from pathlib import Path

import pytest

from fapilot.cli import main, start_app, start_project


def test_start_project_scaffolds_expected_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    start_project("demo")

    assert (tmp_path / "demo/manage.py").exists()
    assert (tmp_path / "demo/config/settings.py").exists()
    assert (tmp_path / "demo/apps/__init__.py").exists()
    assert (tmp_path / "demo/common/pagination.py").exists()
    assert "fapilot" in (tmp_path / "demo/pyproject.toml").read_text(encoding="utf-8")


def test_start_app_scaffolds_django_style_app(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "apps").mkdir()

    start_app("users")

    assert (tmp_path / "apps/users/apps.py").exists()
    assert (tmp_path / "apps/users/api.py").exists()
    assert (tmp_path / "apps/users/migrations/__init__.py").exists()
    assert "UsersConfig" in (tmp_path / "apps/users/apps.py").read_text(encoding="utf-8")



ARCHITECTURE_LAYOUTS = {
    "mvc": "controllers", "mvvm": "viewmodels", "mtv": "templates", "mvp": "presenters",
    "layered": "business/services", "clean": "use_cases", "hexagonal": "core/ports",
    "onion": "domain", "component-based": "components", "microservices": "services/users",
    "monolithic": "application/users", "modular-monolith": "modules/users",
    "event-driven": "event_bus", "cqrs": "write_model", "event-sourcing": "event_store",
    "pac": "agents/control", "hmvc": "modules/main/controllers", "viper": "interactors",
    "flux": "dispatcher", "redux": "reducers",
}


@pytest.mark.parametrize("architecture, folder", ARCHITECTURE_LAYOUTS.items())
def test_architecture_scaffold(tmp_path: Path, monkeypatch, architecture, folder) -> None:
    monkeypatch.chdir(tmp_path)
    start_project("demo", architecture=architecture)
    root = tmp_path / "demo"
    assert (root / folder).is_dir()
    assert (root / "config/asgi.py").is_file()
    assert (root / "common/middleware.py").is_file()
    assert f"Architecture: {architecture}" in (root / "README.md").read_text()
    for source in root.rglob("*.py"):
        compile(source.read_text(), str(source), "exec")


@pytest.mark.parametrize("flag", ["--architecture", "--structure"])
def test_architecture_cli(tmp_path: Path, monkeypatch, flag) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["fapilot", "startproject", "demo", flag, "clean"])
    main()
    assert (tmp_path / "demo/use_cases/__init__.py").is_file()


def test_invalid_architecture_creates_no_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="Unknown architecture"):
        start_project("demo", architecture="unknown")
    assert not (tmp_path / "demo").exists()
    monkeypatch.setattr(
        "sys.argv", ["fapilot", "startproject", "demo", "--architecture", "unknown"]
    )
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert not (tmp_path / "demo").exists()


def test_existing_project_is_preserved(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    start_project("demo", architecture="mvc")
    with pytest.raises(FileExistsError):
        start_project("demo", architecture="clean")
    assert (tmp_path / "demo/controllers").is_dir()
    assert not (tmp_path / "demo/use_cases").exists()


@pytest.mark.parametrize("command, action", [("makemigrations", "migrate"), ("migrate", "upgrade")])
@pytest.mark.parametrize("app", ["models", "reporting"])
def test_migration_cli_selects_model_group(monkeypatch, command, action, app) -> None:
    calls = []
    monkeypatch.setattr("fapilot.db.migrations.subprocess.run", lambda *a, **kw: calls.append(a))
    argv = ["fapilot", command]
    if app != "models":
        argv += ["--app", app]
    monkeypatch.setattr("sys.argv", argv)
    main()
    assert calls == [(["aerich", "-c", "pyproject.toml", "--app", app, action],)]
