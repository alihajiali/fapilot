from pathlib import Path

from fapilot.cli import start_app, start_project


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

