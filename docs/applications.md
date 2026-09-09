# Applications, routing, and lifecycle

[Documentation index](index.md)

## App configuration

```python
# apps/products/apps.py
from fapilot.apps import AppConfig


class ProductsConfig(AppConfig):
    def __init__(self):
        super().__init__(
            name="apps.products",
            label="products",
            verbose_name="Product catalog",
            router_prefix="/api/catalog",
        )

    def ready(self):
        # Synchronous registration work only; ORM startup has not happened yet.
        pass
```

Use `INSTALLED_APPS = ["apps.products.apps.ProductsConfig"]`. Prefer complete
configuration-class paths: dotted package names alone are not resolved like Django
app entries. A bare entry such as `products` resolves to `products.apps.Config`.
Configuration classes must instantiate `AppConfig` or a subclass without arguments.

`label` defaults to the last component of `name`. Labels must be unique, and `models`
is reserved by the ORM builder for migration metadata. The registry loads every app,
then calls synchronous `ready()` hooks. A successful population is idempotent.
Do not perform ORM queries from `ready()`; connections open during ASGI lifespan.

## Router discovery

If `AppConfig.router` is provided, Fapilot uses it. Otherwise it imports
`<app.name>.api` and looks for `router`. The default prefix is
`<API_PREFIX>/<app_label>`; the default tag is the label. A nonempty `router_prefix`
replaces the whole prefix. An empty string currently falls back to the default.

An app without a router can still supply models. Router discovery catches
`ModuleNotFoundError`, including errors caused by missing dependencies inside `api.py`;
a missing route may therefore require manually importing that module to find the error.

`config/urls.py` is not mounted automatically. To use it, add this after the existing
`app = create_app(...)` line in `config/asgi.py`:

```python
from config.urls import router

app.include_router(router)
```

FastAPI routes, dependencies, exception handlers, and middleware can also be added
on the returned app directly.

## Application factory and state

```python
from fapilot import Fapilot
from fapilot.conf import load_settings

framework = Fapilot(load_settings("config.settings"))


async def on_startup(app):
    app.state.ready = True


async def on_shutdown(app):
    app.state.ready = False


framework.events.connect("startup", on_startup)
framework.events.connect("shutdown", on_shutdown)
app = framework.create_fastapi()
```

`create_app(settings)` is the shorthand for constructing `Fapilot` and calling
`create_fastapi()`. `app.state.fapilot` exposes the framework instance, including
`settings`, `registry`, and `events`; it is available after app creation.
In an endpoint, access it with `request.app.state.fapilot`.

The factory:

1. Populates the app registry.
2. Constructs FastAPI with `debug=settings.DEBUG` and its lifespan manager.
3. Stores the framework instance on application state.
4. Calls configured middleware installer functions.
5. Includes app routers.

On normal server startup, lifespan initializes the ORM, optionally generates schemas
when `DEBUG=True`, and emits `startup` with `app=app`. On normal shutdown it emits
`shutdown` and closes ORM connections. Signal receivers run sequentially and their
exceptions propagate. A failed startup receiver or shutdown receiver can interrupt
cleanup in the current implementation; keep these receivers short and reliable.

## Middleware installers

`MIDDLEWARE` is a list of import paths to synchronous functions accepting the FastAPI
app, not Django middleware class paths. For example:

```python
# common/middleware.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware


def install_hosts(app):
    settings = app.state.fapilot.settings
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
```

Add `"common.middleware.install_hosts"` to `MIDDLEWARE` to enforce hosts.
The `ALLOWED_HOSTS` setting alone does not install this behavior.
See [configuration](configuration.md) for cached settings used by built-in helpers.

The ORM enables Tortoise's global fallback so request tasks can access the context
created by the separate lifespan task. Run one active Fapilot ORM lifecycle per
process; concurrent app instances with different database configurations are not
supported by this integration. Sequential isolated tests should close each lifespan.
