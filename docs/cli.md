# CLI reference

[Documentation index](index.md)

The installed `fapilot` entry point and generated `python manage.py` call
`fapilot.cli.main`. Commands use the current working directory. Run app creation,
migrations, and serving from the generated project root.

```bash
fapilot --help
fapilot startproject --help
python manage.py --help
```

The current `fapilot/cli.py` has no module-execution guard; `python -m fapilot.cli`
does not invoke the parser. Use the installed command or generated `manage.py`.

## startproject

```text
fapilot startproject NAME [--architecture CHOICE]
fapilot startproject NAME [--structure CHOICE]
```

Creates a new directory, shared configuration, common helpers, tests package,
management entry point, environment files, packaging metadata, and Docker files.
`--structure` aliases `--architecture`. Choices are:

```text
mvc mvvm mtv mvp layered clean hexagonal onion component-based microservices
monolithic modular-monolith event-driven cqrs event-sourcing pac hmvc viper flux redux
```

The default has no additional architecture folders. See the complete
[layout table](project-structure.md). Choices are case-sensitive. Unknown choices
are rejected by argparse before file creation. An existing destination raises
`FileExistsError`. Parent directories must exist. Generation is not transactional;
a later filesystem error can leave a partial project.

The generated project name is inserted directly into metadata. Use simple names
such as `myproject`; the CLI does not validate distribution-name syntax or escape
arbitrary text. The programmatic equivalent is
`start_project(name: str, architecture: str | None = None)` from `fapilot.cli`.

## startapp

```text
fapilot startapp NAME
```

Creates `apps/NAME`, with models, API router, schemas, config class, helper
placeholders, and tests/migrations packages. It creates `apps/` if missing.
Use valid Python identifiers. A name `order_items` generates `OrderItemsConfig`.
It does not edit `INSTALLED_APPS`, apply an architecture layout, or create database
records. Existing app directories cause an error. Programmatic equivalent:
`start_app(name: str)` from `fapilot.cli`.

## makemigrations

```text
fapilot makemigrations [--name NAME] [--app APP]
```

Runs `aerich -c pyproject.toml --app APP migrate`, adding `--name NAME` when provided.
`APP` defaults to `models`. The app is a Tortoise group label. Initialize migration
history first and review generated migrations before applying them.

## migrate

```text
fapilot migrate [--app APP]
```

Runs `aerich -c pyproject.toml --app APP upgrade`. Default app is `models`.
It upgrades one group; it does not loop through all installed apps or connections.
See [database initialization and multi-group workflow](databases.md).

## runserver

```text
fapilot runserver [--host HOST] [--port PORT]
```

Defaults: host `127.0.0.1`, port `8000`. Runs:

```bash
uvicorn config.asgi:app --host 127.0.0.1 --port 8000 --reload
```

Reload is always enabled. There is no CLI app-path, worker-count, or no-reload option.
Use Uvicorn directly for deployment or a different ASGI module. The parser forwards
the port as a string; Uvicorn handles port validation.

## Failures and extension points

Argparse handles usage errors with exit code 2. Filesystem and subprocess errors are
not caught by a custom CLI error renderer. Child processes run with `check=True`;
a failed Aerich/Uvicorn invocation raises `CalledProcessError`, and a missing executable
raises `FileNotFoundError`.

`CommandRegistry` from `fapilot.management.commands` is a standalone callable map;
it is not connected to CLI command discovery. To expose custom commands, provide a
separate script or extend the parser in your own integration.

## createcachetable

```text
fapilot createcachetable [--cache ALIAS]
```

Loads `config.settings` and creates missing tables for every configured database
cache, or only the selected alias. The connection comes from `OPTIONS.CONNECTION`.
An explicit non-database alias is rejected. Existing tables and their data are preserved;
this does not create databases or run application migrations. See [caching](caching.md).
