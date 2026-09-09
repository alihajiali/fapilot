# Testing

[Documentation index](index.md)

## Install and run

Framework checkout:

```bash
python -m pip install -e ".[dev]"
pytest
```

A generated application can install its own test dependencies:

```bash
python -m pip install pytest httpx
```

HTTPX is optional for normal server operation but required to import
`fapilot.testing.AsyncTestClient`.

## A lifecycle-aware API test

For the products API in [getting started](getting-started.md), create
`tests/test_products.py` in the generated project:

```python
from fastapi.testclient import TestClient

from fapilot import create_app
from fapilot.conf import FapilotSettings


def test_product_crud(tmp_path):
    settings = FapilotSettings(
        DEBUG=True,
        DATABASE_URL=f"sqlite://{tmp_path / 'test.sqlite3'}",
        DATABASES={},
        DATABASE_APPS={},
        INSTALLED_APPS=["apps.products.apps.ProductsConfig"],
        MIDDLEWARE=[],
    )
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.post(
            "/api/products/", json={"name": "Notebook", "price_cents": 500}
        )
        assert response.status_code == 201
        product_id = response.json()["id"]
        response = client.get("/api/products/?limit=10")
        assert response.status_code == 200
        assert response.json()["total"] == 1
        response = client.patch(
            f"/api/products/{product_id}", json={"price_cents": 600}
        )
        assert response.json()["price_cents"] == 600
        assert client.delete(f"/api/products/{product_id}").status_code == 204
        assert client.get(f"/api/products/{product_id}").status_code == 404
```

The context manager starts and stops lifespan, so ORM setup and cleanup happen.
This behavior is also covered by [FastAPI's lifespan testing documentation](https://fastapi.tiangolo.com/advanced/testing-events/).
The temporary database keeps the test away from application data. Explicit empty
connection mappings avoid inheriting database maps from the environment.

## Async tests

`AsyncTestClient(app)` is an async context manager around HTTPX `AsyncClient` and
`ASGITransport`, with base URL `http://testserver`. It does **not** start lifespan.
For tests that use the ORM, enter lifespan explicitly:

```python
import pytest
from fapilot import create_app
from fapilot.conf import FapilotSettings
from fapilot.testing import AsyncTestClient


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_async_products(tmp_path):
    settings = FapilotSettings(
        DEBUG=True,
        DATABASE_URL=f"sqlite://{tmp_path / 'async.sqlite3'}",
        DATABASES={},
        DATABASE_APPS={},
        INSTALLED_APPS=["apps.products.apps.ProductsConfig"],
        MIDDLEWARE=[],
    )
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        async with AsyncTestClient(app) as client:
            response = await client.get("/api/products/")
            assert response.status_code == 200
            assert response.json()["items"] == []
```

Use the asyncio backend because Tortoise and `TaskQueue` rely on asyncio. Keep
async ORM calls within the same event loop as startup and shutdown. For routing-only
tests without database use, skipping lifespan can be intentional.

## Settings isolation

`get_settings` is cached. Clear it before and after tests that alter environment
variables or settings modules. App-local settings do not automatically replace the
settings used by JWT, CORS, and pagination. Patch the consumer's `get_settings` when
a test needs a specific isolated object, for example
`monkeypatch.setattr("fapilot.pagination.get_settings", lambda: settings)`.

## Multiple database testing

Give every connection a separate temporary file. Create/read records through models,
then verify tables and data in the expected file. The framework's
[`tests/test_database.py`](../tests/test_database.py) demonstrates this and checks
invalid mappings. Do not only assert that configuration dictionaries contain aliases;
verify real routing. Migration changes additionally need a disposable-database
initialization, upgrade, and application-startup check.

## Utility and endpoint tests

- Test CRUD success, missing records, invalid input, and permission denials.
- Test filter allowlists and pagination boundaries using FastAPI requests.
- Test signal order and receiver exceptions without needing a server.
- Compare `sse_event` output directly for framing tests.
- Use a WebSocket-capable client to test accepted connections and disconnect cleanup.
- Test password hash/verify round trips against the exact locked dependency versions.

Repository checks are documented in the [contributor guide](contributing.md).
