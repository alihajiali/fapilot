import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from fapilot.admin.auth import check_password, make_password


@pytest.mark.parametrize(
    "password, confirmation, created",
    [("short", "yes", True), ("short", "", False), ("short", "no", False),
     ("a longer password", "", True)],
)
@pytest.mark.parametrize("custom_settings", [False, True])
def test_createsuperuser_project_settings(
    tmp_path, password, confirmation, created, custom_settings
):
    module = "custom_settings" if custom_settings else "config.settings"
    if not custom_settings:
        (tmp_path / "config").mkdir()
        (tmp_path / "config/__init__.py").touch()
    settings_file = tmp_path / (module.replace(".", "/") + ".py")
    database = tmp_path / "staff.sqlite3"
    settings_file.write_text(
        f"ADMIN_ENABLED = True\nDEBUG = True\nDATABASE_URL = 'sqlite://{database}'\n"
    )
    env = os.environ.copy()
    env.pop("FAPILOT_SETTINGS_MODULE", None)
    if custom_settings:
        env["FAPILOT_SETTINGS_MODULE"] = module
    # Launch a script outside the project, like the installed console entry point.
    entry = tmp_path / "bin"
    entry.mkdir()
    script = entry / "fapilot"
    script.write_text("from fapilot.cli import main\nmain()\n")
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    result = subprocess.run(
        [sys.executable, str(script), "createsuperuser"],
        cwd=tmp_path, env=env,
        input=f"ali\nali@gmail.com\n{password}\n{password}\n{confirmation}\n",
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert ("This password is weak" in result.stdout) == (len(password) < 12)
    if not created:
        assert "cancelled" in result.stdout
        assert not database.exists()
        return
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT username, email, password, is_superuser, is_staff, is_active "
            "FROM fapilot_admin_user"
        ).fetchone()
    assert row[:2] == ("ali", "ali@gmail.com")
    assert check_password(password, row[2])
    assert row[3:] == (1, 1, 1)


def test_weak_password_hashing_requires_explicit_override():
    with pytest.raises(ValueError, match="12 characters"):
        make_password("short")
    assert check_password("short", make_password("short", allow_weak=True))
    with pytest.raises(ValueError, match="required"):
        make_password("", allow_weak=True)
