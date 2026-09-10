# Databases, models, and migrations

[Documentation index](index.md)

## Model discovery

Registered apps contribute `<app.name>.models` plus every module listed in
`AppConfig.tortoise_models`. Every module must be importable. Define Tortoise model
classes there; the [first API walkthrough](getting-started.md) has a complete example.
Fapilot also registers `aerich.models` in a reserved group named `models`.

The runtime and generated `config/database.py` both call `build_tortoise_config`.
The resulting dictionary has `connections` and `apps`, following
[Tortoise's named connection configuration](https://tortoise.github.io/connections.html).
A model group's `default_connection` governs its ordinary queries and schema.

`AppConfig.migrations_package` does not set the Aerich migration location and is
not consumed by `build_tortoise_config`. The generated project configures Aerich
under `[tool.aerich]` in `pyproject.toml`.

## Single database

```python
DATABASE_URL = "sqlite://db.sqlite3"
```

All discovered models use `default`. SQLite paths are relative to the process working
directory. For an absolute path, use `sqlite:///absolute/path/db.sqlite3`.
The project installs Tortoise's asyncpg extra for PostgreSQL. Other database engines
may need additional drivers; Fapilot does not install every Tortoise driver.
Connection values accepted by `DATABASES` are URL strings, not engine/credentials dictionaries.

## Multiple databases

In `config/settings.py`:

```python
DATABASES = {
    "default": "sqlite://db.sqlite3",
    "analytics": "sqlite://analytics.sqlite3",
}
INSTALLED_APPS = ["apps.products.apps.ProductsConfig"]
DATABASE_APPS = {
    "products": {"default_connection": "default"},
    "reporting": {
        "default_connection": "analytics",
        "models": ["apps.reports.models", "apps.metrics.models"],
    },
}
```

This routes installed product models to the default database and the two explicit
modules to analytics. Create those modules before startup. An explicit model group
does not need a corresponding `AppConfig`, and it does not add HTTP routes.

The effective connection map is `{"default": DATABASE_URL, **DATABASES}`.
Thus `DATABASES["default"]` wins over the legacy URL; otherwise the fallback stays.
Unused connections are allowed. Installed apps not mentioned in `DATABASE_APPS`
continue to use `default`.

For typed construction outside a settings module:

```python
from fapilot.conf import FapilotSettings
from fapilot.conf.settings import DatabaseAppSettings

settings = FapilotSettings(
    DATABASES={"analytics": "sqlite://analytics.sqlite3"},
    DATABASE_APPS={
        "reporting": DatabaseAppSettings(
            default_connection="analytics", models=["apps.reports.models"]
        )
    },
)
```

## Split models within a feature

Put models needing different databases in separate modules, for example
`apps.catalog.primary_models` and `apps.catalog.audit_models`:

```python
DATABASE_APPS = {
    "catalog": {
        "default_connection": "default",
        "models": ["apps.catalog.primary_models"],
    },
    "catalog_audit": {
        "default_connection": "analytics",
        "models": ["apps.catalog.audit_models"],
    },
}
```

When `catalog` is an installed app, explicit `models` replaces its normally discovered
modules. The ORM app label for the audit models is `catalog_audit`. Relationship
strings use those group labels, such as `"catalog.Product"`.
Do not import/re-export the same model class in modules assigned to different groups.
Fapilot detects repeated module strings across groups, but does not detect all aliases
or re-exported model classes. Keep related models on the same connection;
cross-database joins and atomic transactions are not supplied.

Mapping granularity is a model module/group, not individual class paths in `models`.
There is no automatic tenant selection, read-replica routing, database creation,
or data copying when changing a mapping. Moving an existing model between databases
requires a planned schema and data migration.

## Validation

Configuration building rejects blank connection aliases/URLs, blank or reserved
group labels, unknown connection references, empty explicit module lists, and new
groups without modules. It also rejects a module assigned to two groups.
Pydantic rejects unknown group fields. Missing imports and invalid database URL schemes
are reported later by Tortoise; URL syntax is not fully validated by the settings model.
Error messages for unknown connections do not include connection credentials.

## Debug schemas versus migrations

`DEBUG=True` calls `Tortoise.generate_schemas(safe=True)` at server startup.
This is useful for a disposable first database. It creates missing tables, but is
not a schema migration system and does not establish Aerich migration history.
Use `DEBUG=False` while working with managed migrations.

Generated Aerich configuration:

```toml
[tool.aerich]
tortoise_orm = "config.database.TORTOISE_ORM"
location = "./migrations"
src_folder = "."
```

Run commands from the project root. `apps/products/migrations/` is a scaffold
placeholder; the active migration directory is `migrations/<group>/`.

## Initialize a new development database

For a new project with a registered `products` app and no migration history:

1. Define all models and connection mappings.
2. Set `DEBUG=False` in Python settings, or remove the assignment and use the environment.
3. Initialize the reserved migration metadata group, then your model groups:

```bash
aerich --app models init-db
aerich --app products init-db
```

For the analytics example, also run `aerich --app reporting init-db`.
The generated `pyproject.toml` already contains Aerich's configuration; `aerich init`
is only necessary if that configuration is absent. In a manually configured project:

```bash
aerich init -t config.database.TORTOISE_ORM
```

Initialization creates database tables and initial migration files. Do not use a
fresh-database recipe blindly against an existing production database. If tables
were already created in debug mode, compare the live schema and migration state
before baselining; `safe` table creation does not prove they match.

## Generate and apply changes

After editing a model:

```bash
fapilot makemigrations --app products --name add_description
# Review the new file under migrations/products/ before applying it.
fapilot migrate --app products
```

Repeat for each affected group. `--app` is a Tortoise group label, not a database
alias, Python module, or project name. Omitting it selects `models`, which normally
contains only Aerich metadata; it will not migrate all business model groups.

Fapilot maps `makemigrations` to `aerich migrate` and `migrate` to `aerich upgrade`.
Other operations are available directly through Aerich:

```bash
aerich --app products history
aerich --app products heads
aerich --app products downgrade --help
```

Review downgrade SQL and backup requirements before a rollback. There is no Fapilot
wrapper for database initialization, history, rollback, or running every group's migrations.
Aerich metadata remains on the default connection, so migrations for secondary groups
also need that database accessible. Schema changes and metadata writes across different
connections are not one distributed transaction. See the
[Aerich project documentation](https://github.com/tortoise/aerich) for its additional commands.
