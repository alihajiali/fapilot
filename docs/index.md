# Fapilot documentation

Fapilot is an async backend framework built on FastAPI, Tortoise ORM, and Aerich.
It adds project scaffolding, an app registry, uppercase settings, lifecycle hooks,
and small application helpers. This documentation describes the source in this
repository, including architecture selection and multiple database support.
The package is pre-1.0; check the [changelog](../CHANGELOG.md) when upgrading.

## Start here

1. [Installation and first API](getting-started.md): create a project and run a complete CRUD API.
2. [Project layout and architectures](project-structure.md): generated files and all 20 layouts.
3. [Applications and lifecycle](applications.md): register apps, mount routes, and use startup hooks.
4. [Configuration reference](configuration.md): every setting, defaults, and environment precedence.
5. [Databases and migrations](databases.md): models, multiple connections, schema initialization, migrations.

## Build features

- [HTTP APIs and helpers](http-api.md): CRUD services, schemas, filtering, pagination, middleware, errors.
- [Authentication and permissions](authentication.md): password/JWT helpers and explicit request authentication.
- [Events, background tasks, and realtime](async-features.md): signals, tasks, SSE, and WebSockets.
- [Testing](testing.md): unit tests, lifespan-aware integration tests, and database isolation.

## Reference and operations

- [CLI reference](cli.md): every command, argument, and migration mapping.
- [Python API reference](api-reference.md): public classes, functions, import paths, and behavior.
- [Deployment](deployment.md): environment settings, Uvicorn, containers, migrations, and operations.
- [Troubleshooting and limitations](troubleshooting.md): failure symptoms, checks, and unsupported automation.
- [Contributor and release guide](contributing.md): development, documentation checks, packaging, and publishing.

## What is included

| Area | Implemented behavior |
| --- | --- |
| HTTP | FastAPI app factory, router discovery, dependency injection through FastAPI |
| Data | Tortoise model discovery, named database connections, app/model-group mapping |
| Schema changes | Aerich CLI wrappers for generating and applying migrations |
| Scaffolding | Fixed shared project layout, optional architecture folders, Django-style apps |
| Utilities | CRUD service, pagination, filter allowlist, JSON envelope, CORS installer |
| Authentication | Password hashing and token helpers; permission predicates |
| Async features | In-process signals, asyncio task spawning, SSE formatting, WebSocket broadcasting |

There is no generated admin UI, authentication endpoint, durable job queue, event
broker, or frontend runtime. Architecture folders are organizational starting points.
See [current limitations](troubleshooting.md) before depending on automatic behavior.

## Reading the examples

Shell examples use Bash and assume commands run from the generated project root,
with its virtual environment active, unless stated otherwise. Python examples identify
the file to create or replace. Use complete class paths in `INSTALLED_APPS`.
The walkthrough uses SQLite so it needs no external database service.
