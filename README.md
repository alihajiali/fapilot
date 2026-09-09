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

### Project architecture

Select an architecture when creating a project:

```bash
fapilot startproject myproject --architecture clean
fapilot startproject myproject --structure mvc
```

Omitting the option preserves the default Django-inspired layout. All selections retain
`config/`, `apps/`, `common/`, and `tests/`, and add the following folders:

| Argument | Architecture folders |
| --- | --- |
| `mvc` | `models/`, `views/`, `controllers/` |
| `mvvm` | `models/`, `views/`, `viewmodels/` |
| `mtv` | `models/`, `templates/`, `views/` |
| `mvp` | `models/`, `views/`, `presenters/` |
| `layered` | `presentation/`, `business/services/`, `data_access/`, `database/` |
| `clean` | `entities/`, `use_cases/`, `interfaces/`, `infrastructure/` |
| `hexagonal` | `core/domain/`, `core/ports/`, `adapters/inbound/`, `adapters/outbound/` |
| `onion` | `domain/`, `application/`, `infrastructure/` |
| `component-based` | `components/`, `pages/`, `layouts/`, `state/` |
| `microservices` | `services/users/`, `services/orders/`, `services/payments/`, `shared/` |
| `monolithic` | `application/users/`, `application/products/`, `application/orders/` |
| `modular-monolith` | `modules/users/`, `modules/orders/`, `modules/payments/`, `shared/` |
| `event-driven` | `events/`, `producers/`, `consumers/`, `event_bus/` |
| `cqrs` | `commands/`, `queries/`, `write_model/`, `read_model/` |
| `event-sourcing` | `events/`, `event_store/`, `aggregates/`, `projections/` |
| `pac` | `agents/presentation/`, `agents/abstraction/`, `agents/control/` |
| `hmvc` | `modules/main/models/`, `modules/main/views/`, `modules/main/controllers/` |
| `viper` | `views/`, `interactors/`, `presenters/`, `entities/`, `routers/` |
| `flux` | `actions/`, `dispatcher/`, `stores/`, `views/` |
| `redux` | `actions/`, `reducers/`, `store/`, `selectors/`, `views/` |

`layered` covers N-tier architecture; `hexagonal` covers ports and adapters.
The generated README records the selection and explains its responsibilities.
These are code organization scaffolds: frontend runtimes, independent service deployments,
message brokers, and event persistence must be implemented separately.
`startapp` continues to generate Django-style apps under `apps/`.

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
