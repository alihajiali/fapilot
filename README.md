# Fapilot

Fapilot is an opinionated, async-first backend framework built on FastAPI. It borrows Django's project organization, app registry, settings discipline, scaffolding, and management-command ergonomics while keeping FastAPI's dependency injection, OpenAPI, lifespan, and async runtime model.

## Features

- Django-inspired project and app scaffolding.
- FastAPI application factory with app registry integration.
- Pydantic settings loader with uppercase application settings.
- Tortoise ORM configuration and Aerich migration backend.
- Pagination, filtering, CRUD, permissions, middleware, events, auth, and realtime helpers.
- CLI commands for project creation, app creation, migrations, and local serving.

## Installation

For local development from this repository:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

After installation, the `fapilot` command is available on your shell path:

```bash
fapilot --help
```

You can also run the CLI directly from a checkout:

```bash
python3.12 -m fapilot.cli --help
```

## Quick Start

```bash
python3.12 -m pip install -e .
fapilot startproject myproject
cd myproject
fapilot startapp users
fapilot makemigrations
fapilot migrate
fapilot runserver
```

Core stack:

- FastAPI + Starlette lifespan
- Pydantic v2 + pydantic-settings
- Tortoise ORM
- Aerich migrations through a backend abstraction
- Uvicorn
- pytest, HTTPX, AnyIO
- Ruff and Pyright

This repository contains the reusable framework package. Generated projects contain `config/`, `apps/`, `common/`, `manage.py`, Docker files, `.env`, and a project-local `pyproject.toml`.

## CLI

```bash
fapilot startproject myproject
fapilot startapp users
fapilot makemigrations --name initial
fapilot migrate
fapilot runserver --host 127.0.0.1 --port 8000
```

## Development

```bash
ruff check .
pyright
pytest
python -m build
twine check dist/*
```

## Release

See [RELEASE.md](RELEASE.md) for the release checklist and PyPI publishing flow.

## License

Fapilot is released under the MIT License. See [LICENSE](LICENSE).
