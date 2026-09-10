# Fapilot

Fapilot is an opinionated, async-first backend framework built on FastAPI. It borrows Django's project organization, app registry, settings discipline, scaffolding, and management-command ergonomics while keeping FastAPI's dependency injection, OpenAPI, lifespan, and async runtime model.

## Documentation

Read the [complete documentation](docs/index.md), starting with the
[installation and CRUD walkthrough](docs/getting-started.md).

- [Settings reference](docs/configuration.md) and [applications](docs/applications.md)
- [Project architectures](docs/project-structure.md) and [CLI reference](docs/cli.md)
- [Databases and migrations](docs/databases.md)
- [HTTP helpers](docs/http-api.md), [authentication](docs/authentication.md), and [async features](docs/async-features.md)
- [Testing](docs/testing.md), [deployment](docs/deployment.md), and [troubleshooting](docs/troubleshooting.md)
- [Python API reference](docs/api-reference.md) and [contributor guide](docs/contributing.md)

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

Generated projects also provide `python manage.py --help`. Run the installed
`fapilot` command from a checkout; module execution with `python -m fapilot.cli`
does not invoke the CLI in the current implementation.

## Quick Start

```bash
python3.12 -m pip install -e .
fapilot startproject myproject
cd myproject
fapilot startapp users
# Register apps.users.apps.UsersConfig in config/settings.py first.
fapilot runserver
```

The [walkthrough](docs/getting-started.md) adds models, schemas, and runnable routes.
For schema changes, follow [database initialization and migrations](docs/databases.md).

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

## Multiple databases

`DATABASE_URL` remains the single-database default. Use named URLs and model groups
in `config/settings.py` to distribute models across databases:

```python
DATABASES = {
    "default": "sqlite://db.sqlite3",
    "analytics": "sqlite://analytics.sqlite3",
}
DATABASE_APPS = {
    # Route all models in the installed app with label "users".
    "users": {"default_connection": "default"},
    # A separate model group can list multiple modules without an installed app.
    "reporting": {
        "default_connection": "analytics",
        "models": ["apps.reports.models", "apps.metrics.models"],
    },
}
```

`DATABASES["default"]` takes precedence over `DATABASE_URL`; otherwise the legacy
URL supplies the default connection. Unmapped installed apps continue to use it.
`DATABASE_APPS` keys are Tortoise app labels. Omitting `models` uses the matching
installed app's modules; providing `models` replaces that group's module list.
For models within one app that need different databases, put them in separate
modules and assign each module to one group. Do not re-export those models from a
module discovered by another group. Model relationships use the group label, for
example `"reporting.Report"`; keep related models on the same connection.
Cross-database joins and atomic transactions are not provided.

Both settings also support JSON environment variables and nested values such as
`DATABASES__analytics=sqlite://analytics.sqlite3`. Explicit Python settings take
precedence over environment values. Generated settings include commented examples.
Unknown connections, missing model modules for new groups, and duplicate module
assignments fail during configuration building. The `models` group is reserved for
Aerich metadata on the default database.

Target each model group when generating and applying migrations:

```bash
fapilot makemigrations --app users --name initial
fapilot migrate --app users
fapilot makemigrations --app reporting --name initial
fapilot migrate --app reporting
```

These commands pass the group to Aerich, which uses its configured connection.
The default remains `--app models`. Configure and initialize Aerich for the model
groups before generating migrations; migration commands do not run every group automatically.

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

## Administration workspace

Fapilot includes a responsive light/dark admin with `ModelAdmin` registration across
all project architectures, staff users and groups, permissions, CRUD forms, search,
filters, relationship editing, bulk actions, CSV exports, and audit history.
See the [admin guide](docs/admin.md) for setup, customization, and the runnable showcase.
