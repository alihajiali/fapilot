# HTTP APIs and helpers

[Documentation index](index.md)

Fapilot returns an ordinary FastAPI application. Use FastAPI routers, request models,
response models, dependencies, and exception handlers directly. Start with the
[complete CRUD walkthrough](getting-started.md) for a runnable example.

## CRUD service

`CRUDRouterService[Model, CreateSchema, UpdateSchema](Model)` wraps common Tortoise
operations. Despite its name, it does not create an `APIRouter` or endpoints.

| Method | Behavior |
| --- | --- |
| `await list(offset=0, limit=20, filters=None)` | Filters then offsets/limits the query; no implicit ordering |
| `await count(filters=None)` | Counts matching rows |
| `await get(object_id)` | Looks up `id=object_id`; returns `None` when missing |
| `await create(data)` | Creates a row from `data.model_dump()` |
| `await update(instance, data)` | Applies `model_dump(exclude_unset=True)` and saves |
| `await delete(instance)` | Deletes the instance |

The service assumes a field named `id` for `get`. It does not implement authorization,
404 responses, transaction boundaries, uniqueness-error translation, or output serialization.
Explicit null values in updates are applied; validate them against model constraints.
Use schemas with `ConfigDict(from_attributes=True)` to serialize model instances.
For deterministic pagination, add an ordered query in your repository/service.

## Pagination

```python
from fastapi import APIRouter
from fapilot.pagination import LimitOffset, Pagination

router = APIRouter()


@router.get("/page-info")
async def page_info(page: LimitOffset = Pagination):
    return {"limit": page.limit, "offset": page.offset}
```

Through FastAPI, `limit` must be at least 1 and `offset` at least 0. Omitted limit uses
`DEFAULT_PAGE_SIZE`; values above `MAX_PAGE_SIZE` are clamped. Defaults are 20 and 100.
`Page[T]` has `items`, `total`, `limit`, and `offset`. Supply all four fields yourself;
it does not count or fetch records. `Pagination` is a prebuilt `Depends` object.
`pagination_params` reads cached global settings; see [configuration](configuration.md).

## Filter allowlists

```python
from fapilot.filtering import pick_filters

filters = pick_filters(
    {"name": "Notebook", "price_cents__gte": 100, "unknown": "ignored", "id": None},
    allowed={"name", "price_cents__gte", "id"},
)
# {"name": "Notebook", "price_cents__gte": 100}
```

This helper removes unlisted keys and `None` values. It preserves `False`, `0`, and
empty strings. It does not convert strings, validate field types, or define public
search semantics. Validate request parameters before forwarding allowed filters.

## Responses and errors

`ok(data=None, status_code=200)` returns `JSONResponse({"data": data})`.
Pass JSON-compatible values; a Tortoise object, datetime, or Pydantic model is not
converted automatically by this helper. For a Pydantic object, use
`ok(schema.model_dump(mode="json"))`. It is separate from the `Page` format.

Raise FastAPI `HTTPException` for HTTP errors. `FapilotError` and
`ConfigurationError` are plain exception classes, not automatically translated
responses. Install your own handlers if you use them at request boundaries:

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fapilot.exceptions import FapilotError

# Add after creating app in config/asgi.py.
async def handle_domain_error(request: Request, exc: FapilotError):
    return JSONResponse({"detail": "Request could not be completed"}, status_code=400)

# app.add_exception_handler(FapilotError, handle_domain_error)
```

Choose status codes and safe error messages to fit the domain. The framework does
not automatically map database errors to 400 or 409.

## CORS and host validation

Add `"fapilot.middleware.install_cors"` to `MIDDLEWARE` and configure
`CORS_ALLOWED_ORIGINS`. The generated alias `common.middleware.install_cors` does
the same thing. With a nonempty origin list, it installs CORS middleware with
credentials enabled and all methods/headers allowed. With an empty list it installs
nothing. Use explicit origins when credentials are enabled.

Host validation is separate: `ALLOWED_HOSTS` alone is not enforced. Use the
[custom installer example](applications.md) if the application needs it.
