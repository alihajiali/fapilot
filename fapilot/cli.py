from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from fapilot.architectures import ARCHITECTURE_GUIDANCE, ARCHITECTURES
from fapilot.db.migrations import AerichMigrationBackend


def main() -> None:
    parser = argparse.ArgumentParser(prog="fapilot")
    subparsers = parser.add_subparsers(dest="command", required=True)
    startproject = subparsers.add_parser("startproject")
    startproject.add_argument("name")
    startproject.add_argument(
        "--architecture", "--structure",
        choices=sorted(ARCHITECTURES),
        help="Project architecture layout (default: existing Django-inspired layout).",
    )
    startapp = subparsers.add_parser("startapp")
    startapp.add_argument("name")
    makemigrations = subparsers.add_parser("makemigrations")
    makemigrations.add_argument("--name")
    subparsers.add_parser("migrate")
    runserver = subparsers.add_parser("runserver")
    runserver.add_argument("--host", default="127.0.0.1")
    runserver.add_argument("--port", default="8000")
    args = parser.parse_args()

    if args.command == "startproject":
        start_project(args.name, architecture=args.architecture)
    elif args.command == "startapp":
        start_app(args.name)
    elif args.command == "makemigrations":
        AerichMigrationBackend().makemigrations(args.name)
    elif args.command == "migrate":
        AerichMigrationBackend().migrate()
    elif args.command == "runserver":
        subprocess.run(
            ["uvicorn", "config.asgi:app", "--host", args.host, "--port", args.port, "--reload"],
            check=True,
        )


def start_project(name: str, architecture: str | None = None) -> None:
    if architecture is not None and architecture not in ARCHITECTURES:
        raise ValueError(f"Unknown architecture: {architecture}")
    root = Path(name)
    root.mkdir()
    for directory in ["config", "apps", "common", "tests"]:
        (root / directory).mkdir()
        (root / directory / "__init__.py").write_text("", encoding="utf-8")
    _write(root / "manage.py", MANAGE)
    _write(root / "config/settings.py", SETTINGS)
    _write(root / "config/database.py", DATABASE)
    _write(root / "config/urls.py", URLS)
    _write(root / "config/asgi.py", ASGI)
    _write(root / "config/logging.py", "LOGGING = {}\n")
    _write(root / "common/crud.py", "from fapilot.crud import CRUDRouterService\n")
    _write(root / "common/pagination.py", "from fapilot.pagination import Page, Pagination\n")
    _write(root / "common/filtering.py", "from fapilot.filtering import pick_filters\n")
    _write(root / "common/exceptions.py", "from fapilot.exceptions import FapilotError\n")
    _write(
        root / "common/permissions.py",
        "from fapilot.permissions import AllowAny, IsAuthenticated\n",
    )
    _write(root / "common/middleware.py", "from fapilot.middleware import install_cors\n")
    _write(root / "common/responses.py", "from fapilot.responses import ok\n")
    _write(root / "common/events.py", "from fapilot.events import SignalDispatcher\n")
    _write(root / "common/models.py", "from tortoise import fields, models\n")
    _write(root / "common/schemas.py", "from pydantic import BaseModel, ConfigDict\n")
    _write(root / "common/utils.py", "\n")
    _write(root / ".env", ENV)
    _write(root / ".env.example", ENV)
    _write(root / ".gitignore", GITIGNORE)
    readme = PROJECT_README.format(name=name)
    if architecture is not None:
        for directory in ARCHITECTURES[architecture]:
            package = root
            for part in Path(directory).parts:
                package /= part
                package.mkdir(exist_ok=True)
                if package.name != "templates":
                    _write(package / "__init__.py", "")
        layout = "\n".join(f"- `{directory}/`" for directory in ARCHITECTURES[architecture])
        readme += (
            f"\n## Architecture: {architecture}\n\n"
            f"{ARCHITECTURE_GUIDANCE[architecture]}\n\n{layout}\n\n"
            "These folders are organization scaffolds for application code. "
            "Add implementations and integrations as needed; no frontend runtime, "
            "message broker, event persistence, or service deployment is provisioned.\n\n"
            "`config/` contains FastAPI configuration, `common/` contains framework helpers, "
            "and `tests/` contains project tests. `fapilot startapp` continues to create "
            "Django-style apps under `apps/`; register those apps in `INSTALLED_APPS`.\n"
        )
    _write(root / "README.md", readme)
    _write(root / "Dockerfile", DOCKERFILE)
    _write(root / "docker-compose.yml", COMPOSE)
    _write(root / "pyproject.toml", PROJECT_PYPROJECT.format(name=name))


def start_app(name: str) -> None:
    app_dir = Path("apps") / name
    app_dir.mkdir(parents=True)
    (app_dir / "tests").mkdir()
    (app_dir / "migrations").mkdir()
    for file_name, content in APP_FILES.items():
        class_name = name.title().replace("_", "")
        _write(app_dir / file_name, content.format(name=name, class_name=class_name))
    _write(app_dir / "tests/__init__.py", "")
    _write(app_dir / "migrations/__init__.py", "")


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


MANAGE = """#!/usr/bin/env python
from fapilot.cli import main

if __name__ == "__main__":
    main()
"""

SETTINGS = '''from fapilot.conf import FapilotSettings

DEBUG = True
SECRET_KEY = "change-me"
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
DATABASE_URL = "sqlite://db.sqlite3"
INSTALLED_APPS = []
MIDDLEWARE = ["common.middleware.install_cors"]
CORS_ALLOWED_ORIGINS = []
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
API_PREFIX = "/api"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
AUTH_USER_MODEL = "users.User"
JWT_SETTINGS = FapilotSettings().JWT_SETTINGS
LOGGING = {}
'''

DATABASE = """import os

from fapilot.apps import AppRegistry
from fapilot.conf import load_settings
from fapilot.db.tortoise import build_tortoise_config

settings = load_settings("config.settings")
registry = AppRegistry()
registry.populate(settings.INSTALLED_APPS)
TORTOISE_ORM = build_tortoise_config(settings, registry)
"""

URLS = """from fastapi import APIRouter

router = APIRouter()
"""

ASGI = """import os

from fapilot import create_app
from fapilot.conf import load_settings

os.environ.setdefault("FAPILOT_SETTINGS_MODULE", "config.settings")
app = create_app(load_settings("config.settings"))
"""

ENV = """DEBUG=true
SECRET_KEY=change-me
DATABASE_URL=sqlite://db.sqlite3
"""

GITIGNORE = """.venv/
__pycache__/
.env
db.sqlite3
.ruff_cache/
.pytest_cache/
"""

PROJECT_README = """# {name}

Generated by Fapilot.

```bash
uv sync
fapilot startapp users
fapilot runserver
```
"""

PROJECT_PYPROJECT = '''[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fapilot"]

[tool.aerich]
tortoise_orm = "config.database.TORTOISE_ORM"
location = "./migrations"
src_folder = "."
'''

DOCKERFILE = """FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install fapilot
CMD ["uvicorn", "config.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
"""

COMPOSE = """services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
    ports:
      - "5432:5432"
"""

APP_FILES = {
    "__init__.py": "",
    "apps.py": """from fapilot.apps import AppConfig


class {class_name}Config(AppConfig):
    def __init__(self) -> None:
        super().__init__(name="apps.{name}", label="{name}")
""",
    "models.py": "from tortoise import fields, models\n\n\n# Define models here.\n",
    "schemas.py": "from pydantic import BaseModel, ConfigDict\n\n\n# Define schemas here.\n",
    "api.py": """from fastapi import APIRouter

router = APIRouter()
""",
    "services.py": "",
    "repositories.py": "",
    "permissions.py": "from fapilot.permissions import AllowAny, IsAuthenticated\n",
    "dependencies.py": "",
    "signals.py": "",
    "admin.py": "",
}
