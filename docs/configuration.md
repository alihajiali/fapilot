# Configuration reference

[Documentation index](index.md)

## Loading and precedence

`FapilotSettings` is a Pydantic Settings model. `load_settings("config.settings")`
imports uppercase, nonprivate attributes from that Python module and validates them.
Without an explicit module, it checks `FAPILOT_SETTINGS_MODULE`; without either,
it constructs `FapilotSettings()` from the environment and defaults.

The usual precedence, highest first, is:

1. Explicit constructor values, including values imported from a settings module.
2. Process environment variables.
3. `.env` in the current working directory.
4. Field defaults.

Names are case-sensitive. Nested keys use `__`; lists and dictionaries accept JSON.
Unrecognized top-level fields are ignored. Unknown fields within a `DATABASE_APPS`
group are rejected. `DEBUG=release`, `prod`, and `production` are treated as false,
in addition to normal Pydantic boolean parsing.

The generated Python settings explicitly set `DEBUG`, `SECRET_KEY`, and
`DATABASE_URL`. Editing only `.env` will not override those assignments. For an
environment-driven project, remove the deployment-specific assignments from
`config/settings.py`; keep app registrations and other code-level choices there.
An example `.env` after removing conflicting Python assignments:

```dotenv
DEBUG=false
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=sqlite://db.sqlite3
CORS_ALLOWED_ORIGINS=["https://app.example.com"]
DATABASES__analytics=sqlite://analytics.sqlite3
DATABASE_APPS__reporting__default_connection=analytics
DATABASE_APPS__reporting__models=["apps.reports.models"]
JWT_SETTINGS__access_token_expire_minutes=15
```

If `CORS_ALLOWED_ORIGINS` is still defined in the Python module, remove it too for
the environment value to win. Never print the settings object into application logs;
it contains secrets and connection URLs.

## All framework settings

| Setting | Type / default | Current consumer |
| --- | --- | --- |
| `DEBUG` | `bool`, `False` | FastAPI debug mode and automatic safe ORM schema generation |
| `SECRET_KEY` | `str`, `"change-me"` | JWT signing/decoding; replace before issuing real tokens |
| `ALLOWED_HOSTS` | `list[str]`, localhost and 127.0.0.1 | Configuration only unless you install host middleware |
| `DATABASE_URL` | `str`, `"sqlite://db.sqlite3"` | Fallback default ORM connection |
| `DATABASES` | `dict[str, str]`, `{}` | Named connection URLs; explicit `default` overrides fallback |
| `DATABASE_APPS` | model-group mapping, `{}` | Per-group modules and connection selection |
| `INSTALLED_APPS` | `list[str]`, `[]` | App configuration class paths |
| `MIDDLEWARE` | `list[str]`, `[]` | Middleware installer paths |
| `CORS_ALLOWED_ORIGINS` | `list[str]`, `[]` | Built-in CORS installer, when enabled |
| `TIME_ZONE` | `str`, `"UTC"` | Stored only; ORM config builder does not forward it |
| `LANGUAGE_CODE` | `str`, `"en-us"` | Stored only; no translation middleware |
| `API_PREFIX` | `str`, `"/api"` | Default app router prefix |
| `DEFAULT_PAGE_SIZE` | `int`, `20` | Pagination limit when omitted |
| `MAX_PAGE_SIZE` | `int`, `100` | Pagination limit clamp |
| `AUTH_USER_MODEL` | `str`, `"users.User"` | Stored only; does not create or resolve a user model |
| `JWT_SETTINGS` | `JWTSettings` | JWT helpers; see below |
| `LOGGING` | `dict[str, Any]`, `{}` | Stored only; apply logging configuration explicitly |

Generated projects set `DEBUG=True` and include `common.middleware.install_cors`
in `MIDDLEWARE`, unlike the framework defaults. Pagination setting values are plain
integers without additional positivity validation; configure positive values.

## JWT settings

Import `JWTSettings` from `fapilot.conf.settings`.

| Field | Default | Behavior |
| --- | --- | --- |
| `algorithm` | `"HS256"` | Signing algorithm and accepted decode algorithm |
| `access_token_expire_minutes` | `30` | Token expiration offset |
| `issuer` | `"fapilot"` | Included in issued tokens; not explicitly checked by the decode helper |

Python module example:

```python
JWT_SETTINGS = {
    "algorithm": "HS256",
    "access_token_expire_minutes": 15,
    "issuer": "my-service",
}
```

The generated `JWT_SETTINGS = FapilotSettings().JWT_SETTINGS` reads the settings
model at module import time. See [authentication](authentication.md) for claim behavior.

## Database group settings

`DatabaseAppSettings` is imported from `fapilot.conf.settings`.

| Field | Type / default | Meaning |
| --- | --- | --- |
| `default_connection` | `str`, `"default"` | Key in the effective connection map |
| `models` | `list[str]` or `None` | Explicit module list, or matching installed app modules when omitted |

Plain dictionaries work in settings modules and environment JSON. In typed Python
code that calls `FapilotSettings(...)` directly, construct `DatabaseAppSettings`
instances to satisfy static type checkers. See [databases](databases.md) for examples.

## Cached settings and application instances

`get_settings()` caches one settings instance using `lru_cache`. Call
`get_settings.cache_clear()` after changing environment variables during tests.
There is no file watcher that reloads this cache independently of process restart.

The ORM and app factory use the settings passed to the application. JWT helpers,
pagination, and the CORS installer call global `get_settings()` themselves.
Passing a different settings object to `create_app()` does not replace that cache.
For consistent behavior, use the same `FAPILOT_SETTINGS_MODULE` for the process and
the app factory. For isolated tests, patch the helper module's `get_settings` or
set the environment and clear the cache before constructing the app.

## Cache settings

`CACHES` maps aliases to `CacheSettings` (`fapilot.conf.settings`); a `default` alias
is required. It defaults to a local-memory cache. See [caching](caching.md).

| Cache field | Default |
| --- | --- |
| `BACKEND` | `fapilot.cache.backends.locmem.LocMemCache` |
| `LOCATION` | `fapilot-default` |
| `TIMEOUT` | `300` seconds; `None` means no expiry |
| `OPTIONS` | `{}`; backend-specific constructor options |
| `KEY_PREFIX` | Empty string |
| `VERSION` | `1` |
| `KEY_FUNCTION` | `None`; optional callable or import path |

App-local cache handlers use the settings passed to the factory. The module-level
`cache` and `caches` convenience objects independently use `get_settings()`.

## Authentication and administration settings

These options configure the [authentication](authentication.md) and [admin](admin.md)
integrations alongside caching:

| Setting | Default | Purpose |
| --- | --- | --- |
| `AUTHENTICATION_BACKENDS` | `[]` | Ordered backend paths or `AuthenticationBackendSettings` entries |
| `ADMIN_ENABLED` | `False` | Enables admin discovery, routes, and built-in model registration |
| `ADMIN_URL` | `/admin` | Admin route prefix |
| `ADMIN_SITE` | `fapilot.admin.site` | Import path to an `AdminSite` instance |
| `ADMIN_MODULES` | `[]` | Additional explicit admin registration modules |
| `ADMIN_SECURE_COOKIES` | `True` | Requires HTTPS for admin session cookies |
| `ADMIN_SESSION_SECONDS` | `3600` | Session lifetime, constrained to 60–86400 seconds |
