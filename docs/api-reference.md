# Python API reference

[Documentation index](index.md)

This reference covers the public framework primitives. Generated template constants,
private methods, and third-party APIs are outside the public API surface.
See the linked guides for complete examples.

## Application and imports

| Import | API | Contract |
| --- | --- | --- |
| `fapilot` | `create_app(settings=None) -> FastAPI` | Creates a framework instance and configured FastAPI app |
| `fapilot` | `Fapilot(settings=None)` | Holds `settings`, `registry`, and `events` |
| `fapilot` | `__version__` | Package version string |
| `fapilot.core.application` | `import_string(dotted_path) -> Callable` | Imports final attribute; invalid path raises `ImportError` |

`Fapilot.setup() -> None` populates its registry. `create_fastapi() -> FastAPI`
performs setup and installs lifespan, middleware, and routers. The application is
available at `app.state.fapilot`. See [applications](applications.md).

## Configuration

| Import from `fapilot.conf` | Signature / behavior |
| --- | --- |
| `FapilotSettings` | Pydantic Settings model; [all fields and defaults](configuration.md) |
| `load_settings(settings_module: str \| None = None)` | Explicit module, environment module, or environment/default settings |
| `get_settings()` | Cached settings accessor; exposes `.cache_clear()` |

Import `JWTSettings` and `DatabaseAppSettings` from `fapilot.conf.settings`.
Their fields are listed in the [configuration reference](configuration.md).

## Apps

Import `AppConfig` and `AppRegistry` from `fapilot.apps`.

| `AppConfig` field | Type / default |
| --- | --- |
| `name` | Required `str`, importable app package |
| `label` | `str` or `None`; defaults through `app_label` to final name component |
| `verbose_name` | `str` or `None`; metadata only |
| `router` | `APIRouter` or `None` |
| `router_prefix` | `str` or `None` |
| `tortoise_models` | `list[str]`, independent empty list per instance |
| `migrations_package` | `str` or `None`; not used by main ORM builder |

`AppConfig.app_label` is a property. `ready()` is a synchronous overridable hook.
`as_tortoise_app()` returns a dictionary of `tortoise_models`, appending
`migrations_package` if set, with connection `default`. This convenience method does
not add `<name>.models` or apply settings mappings and is not used by the main ORM builder.

| `AppRegistry` method | Behavior |
| --- | --- |
| `populate(installed_apps: Iterable[str])` | Loads configurations, checks duplicates, calls ready hooks once |
| `get_app(label: str) -> AppConfig` | Looks up a label; missing key raises `KeyError` |
| `get_apps() -> list[AppConfig]` | Returns registered configs in insertion order |

`AppRegistry.ready` indicates successful population. A duplicate label raises
`RuntimeError`; a config of the wrong type raises `TypeError`; import errors propagate.

## Database integration

Import from `fapilot.db.tortoise`:

| Function | Behavior |
| --- | --- |
| `build_tortoise_config(settings, registry) -> dict` | Builds connections and model groups, validates mappings |
| `await init_orm(settings, registry)` | Initializes Tortoise and, in debug mode, generates safe schemas |
| `await close_orm()` | Closes all Tortoise connections |

Import `MigrationBackend` and `AerichMigrationBackend` from `fapilot.db`.
`MigrationBackend` defines abstract synchronous methods `init()`,
`makemigrations(name=None)`, and `migrate()`.

`AerichMigrationBackend(config="pyproject.toml", app="models",
tortoise_config_path="config.database.TORTOISE_ORM")` implements those methods via
subprocess. `init()` calls Aerich `init -t`; it does not call `init-db`.
`makemigrations` calls `migrate`; `migrate` calls `upgrade`. Command failure propagates.
See [databases](databases.md) and [CLI](cli.md).

## HTTP utilities

| Import | Public API |
| --- | --- |
| `fapilot.crud` | `CRUDRouterService[ModelT, CreateSchemaT, UpdateSchemaT](model)` |
| `fapilot.pagination` | `Page[T](items, total, limit, offset)` Pydantic model |
| `fapilot.pagination` | `LimitOffset(limit, offset)` Pydantic model |
| `fapilot.pagination` | `pagination_params(limit=None, offset=0)` FastAPI dependency function |
| `fapilot.pagination` | `Pagination` prebuilt `Depends(pagination_params)` |
| `fapilot.filtering` | `pick_filters(params: dict, allowed: set[str]) -> dict` |
| `fapilot.responses` | `ok(data=None, *, status_code=200) -> JSONResponse` |
| `fapilot.middleware` | `install_cors(app: FastAPI) -> None` |
| `fapilot.exceptions` | `FapilotError(Exception)`, `ConfigurationError(FapilotError)` |

CRUD methods and limitations are listed in [HTTP APIs](http-api.md).
`pagination_params` is intended for FastAPI dependency injection: its Python defaults
are `Query` objects, so direct calls should pass explicit numeric limit and offset.
No default exception handlers are installed for the framework exception classes.

## Authentication and permissions

| Import | API | Behavior |
| --- | --- | --- |
| `fapilot.auth` | `hash_password(password: str) -> str` | Synchronous Passlib bcrypt hash |
| `fapilot.auth` | `verify_password(password: str, hashed_password: str) -> bool` | Synchronous hash verification |
| `fapilot.auth` | `create_access_token(subject: str, claims: dict \| None = None) -> str` | JWT with configured expiry and optional claims |
| `fapilot.auth` | `decode_access_token(token: str) -> dict \| None` | Decode or `None` on `JWTError` |
| `fapilot.permissions` | `Permission` | Protocol: `async has_permission(request) -> bool` |
| `fapilot.permissions` | `AllowAny()` | Always permits |
| `fapilot.permissions` | `IsAuthenticated()` | Checks `request.state.user is not None` |
| `fapilot.permissions.base` | `await require_permissions(request, *permissions)` | Sequential checks; HTTP 403 on denial |

See [authentication](authentication.md) for request wiring, claim validation, and
verified password-backend compatibility limitations.

## Async primitives

| Import | API | Behavior |
| --- | --- | --- |
| `fapilot.events` | `SignalDispatcher()` | Independent in-process receiver registry |
| `SignalDispatcher` instance | `connect(signal: str, receiver)` | Append sync/async receiver |
| `SignalDispatcher` instance | `await emit(signal: str, **payload)` | Sequential delivery, exceptions propagate |
| `fapilot.background` | `TaskQueue()` | Thin asyncio task helper |
| `TaskQueue` instance | `spawn(func, *args, **kwargs) -> asyncio.Task` | Schedules coroutine callable in running loop |
| `fapilot.realtime` | `sse_event(data, *, event=None, event_id=None) -> str` | SSE formatting; nonstrings JSON-encoded |
| `fapilot.realtime` | `EventSourceResponse(content: AsyncIterable[str])` | StreamingResponse with SSE content type |
| `fapilot.realtime` | `WebSocketHub()` | In-process socket set |
| `WebSocketHub` instance | `await connect(websocket)` | Accepts and stores socket |
| `WebSocketHub` instance | `disconnect(websocket)` | Discards socket without closing |
| `WebSocketHub` instance | `await broadcast_text(message: str)` | Sequential sends; removes RuntimeError failures |

See [async features](async-features.md) for examples and process/lifecycle constraints.

## Testing and commands

`fapilot.testing.AsyncTestClient(app)` is an async context manager yielding an HTTPX
`AsyncClient`. It requires HTTPX and does not run lifespan. See [testing](testing.md).

`fapilot.management.commands.CommandRegistry()` exposes
`register(name: str, command: Callable[..., None])` and `get(name)`. Registering an
existing name replaces its callable; looking up a missing name raises `KeyError`.
It does not integrate with the built-in CLI.

`fapilot.cli` exposes `main()`, `start_project(name, architecture=None)`, and
`start_app(name)`. `fapilot.architectures.ARCHITECTURES` maps supported slugs to folder
tuples; `ARCHITECTURE_GUIDANCE` maps them to descriptions. See [CLI](cli.md).
