# Troubleshooting and current limitations

[Documentation index](index.md)

## Installation and CLI

| Symptom | Check and action |
| --- | --- |
| `fapilot: command not found` | Activate the environment where the package is installed; run `python -m pip show fapilot` |
| `python -m fapilot.cli` prints nothing | The module has no execution guard; use `fapilot` or generated `python manage.py` |
| Architecture flag rejected | Check installed version and `fapilot startproject --help`; use a listed lowercase slug |
| `FileExistsError` during scaffolding | Destination already exists; select a new directory or inspect the partial scaffold |
| Import errors for generated app | Use a valid Python identifier and run from project root |
| `aerich` or `uvicorn` missing | Install framework dependencies in the active environment; check executable availability |

## Configuration and routing

| Symptom | Check and action |
| --- | --- |
| `.env` edit has no effect | Python settings have higher precedence; remove conflicting literals and restart |
| Settings appear stale in tests | Clear `get_settings.cache_clear()` before and after environment changes |
| Pagination/CORS/JWT use unexpected settings | Those helpers use global cached settings, not necessarily app-local settings |
| New app has no routes | Add the full config class path to `INSTALLED_APPS`; define/export `api.router` |
| App route still missing | Import `apps.<name>.api` directly to expose errors hidden by router discovery |
| `config/urls.py` routes absent | Include that router manually in the ASGI entry point |
| Duplicate app label | Give configurations unique labels |
| `models` label rejected | It is reserved for Aerich metadata; choose another app/group label |
| Host or language setting does nothing | These settings do not automatically install middleware |

## Database and migrations

| Symptom | Check and action |
| --- | --- |
| Unknown connection | Group `default_connection` must match a named effective connection |
| New group needs model modules | Specify `models` unless the label matches an installed app |
| Model assigned to multiple apps | Assign each module to one group and remove cross-group model re-exports |
| Missing model module | Create/import the module referenced by app discovery or `DATABASE_APPS` |
| Table does not exist | Run database initialization/migrations; debug schema creation only runs in lifespan |
| Column missing after changing a model | Debug schema generation does not alter existing tables; generate/apply migrations |
| Migration reports no model changes | Select the business group using `--app`; default `models` tracks metadata |
| Migration directory unexpected | Active location is `./migrations`, not `apps/<name>/migrations` |
| Secondary database migration fails | Check both secondary connection and default connection used for metadata |
| Database test fails before first request | Ensure lifespan runs and all test connections point to disposable databases |

Connection alias mapping does not create a PostgreSQL database or move existing data.
Avoid dumping complete connection configurations while debugging credentials.
See [database workflows](databases.md) for initialization and upgrades.

## Authentication and async helpers

| Symptom | Check and action |
| --- | --- |
| Password hash fails with a short password | Passlib 1.7.4/bcrypt 5.0.0 failed in validation; verify and lock compatible versions |
| `IsAuthenticated` always denies | Populate `request.state.user` through an authentication dependency |
| Invalid token returns `None` | Check secret, algorithm, expiry, and claim validity; do not expose tokens in logs |
| Background work disappears | `TaskQueue` is process-local asyncio scheduling, not persistent work storage |
| WebSocket clients on different workers do not see broadcasts | Each hub is in-process; add external messaging for shared delivery |
| Signal stops after one receiver | Receiver exceptions propagate and prevent later calls |
| ORM not initialized in `AsyncTestClient` | Enter `app.router.lifespan_context(app)` explicitly |
| ORM cleanup skipped after hook failure | Current lifecycle cleanup can be interrupted by startup/shutdown receiver errors |

## Scope of current implementation

- Architecture selection creates folders; it does not enforce or implement an architecture.
- Generated `admin.py`, `signals.py`, and `config/urls.py` do not activate features by themselves.
- `AUTH_USER_MODEL`, `TIME_ZONE`, `LANGUAGE_CODE`, and `LOGGING` are not fully wired consumers.
- CRUD helpers do not create routes, authorize requests, or convert database errors to HTTP errors.
- One active Fapilot ORM lifecycle per process is supported; concurrent isolated apps are not.
- Model groups are module-based; no per-request tenant routing, replica routing, or cross-database joins.
- Migration commands operate on one group; there is no all-groups or rollback wrapper.
- No built-in login/refresh/revocation endpoints or automatic token-to-user middleware.
- No durable tasks, distributed event bus, replay store, rooms, or shared WebSocket registry.
- Framework testing helpers require the optional HTTPX dependency and do not start lifespan.
- Filesystem scaffolding is not atomic and names are not comprehensively validated.

## Reporting a problem

Include the package version, Python version, relevant dependency versions, exact
command, minimal reproduction, expected/actual behavior, and a sanitized traceback.
Do not include real secrets or customer data. Use the repository issue tracker for
ordinary defects. Follow the [security policy](../SECURITY.md) for private vulnerability
reporting; do not post suspected vulnerabilities in public issues.
