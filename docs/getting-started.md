# Installation and first API

[Documentation index](index.md)

## Requirements

The project declares Python 3.12 or newer. Repository CI tests Python 3.12 and 3.13.
Use one of those versions for a setup matching CI. SQLite needs no separate server;
PostgreSQL is optional. Framework dependencies include FastAPI, Tortoise ORM, Aerich,
Uvicorn, and Pydantic Settings. HTTPX and pytest are development dependencies.

## Install from this checkout

From the Fapilot repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
fapilot --help
```

For a published release, install `fapilot` in a virtual environment with
`python -m pip install fapilot`. A published version may not contain the latest
checkout features; verify `fapilot startproject --help` for architecture support.
On Windows, activate with `.venv\Scripts\Activate.ps1` in PowerShell.

## Create a project and app

Choose an empty parent directory for the generated project while keeping the
Fapilot virtual environment active:

```bash
fapilot startproject demo --architecture layered
cd demo
fapilot startapp products
```

The architecture option is optional. It adds folders; `startapp` still writes to
`apps/products/`. The framework does not automatically register new apps.
In `config/settings.py`, replace `INSTALLED_APPS = []` with:

```python
INSTALLED_APPS = ["apps.products.apps.ProductsConfig"]
```

Keep `DEBUG = True` for this disposable local walkthrough. On startup this creates
missing tables. It does not migrate existing columns; use [Aerich](databases.md)
for managed schema changes and production.

## Define the model

Replace `apps/products/models.py`:

```python
from tortoise import fields, models


class Product(models.Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    price_cents = fields.IntField()
```

Replace `apps/products/schemas.py`:

```python
from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price_cents: int = Field(ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    price_cents: int | None = Field(default=None, ge=0)


class ProductOut(ProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
```

## Add CRUD routes

Replace `apps/products/api.py`:

```python
from fastapi import APIRouter, HTTPException, Response

from fapilot.crud import CRUDRouterService
from fapilot.pagination import LimitOffset, Page, Pagination

from .models import Product
from .schemas import ProductCreate, ProductOut, ProductUpdate

router = APIRouter()
service = CRUDRouterService[Product, ProductCreate, ProductUpdate](Product)


@router.get("/", response_model=Page[ProductOut])
async def list_products(page: LimitOffset = Pagination):
    rows = await service.list(offset=page.offset, limit=page.limit)
    return Page[ProductOut](
        items=[ProductOut.model_validate(row) for row in rows],
        total=await service.count(),
        limit=page.limit,
        offset=page.offset,
    )


@router.post("/", response_model=ProductOut, status_code=201)
async def create_product(data: ProductCreate):
    return await service.create(data)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int):
    product = await service.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, data: ProductUpdate):
    # Omitted fields are unchanged; explicit null is invalid for this model.
    if any(value is None for value in data.model_dump(exclude_unset=True).values()):
        raise HTTPException(status_code=422, detail="Product fields cannot be null")
    product = await get_product(product_id)
    return await service.update(product, data)


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: int):
    product = await get_product(product_id)
    await service.delete(product)
    return Response(status_code=204)
```

The registry discovers `apps.products.api.router` and mounts it at `/api/products`.
The service performs database operations; route creation and HTTP errors are explicit.

## Run and try it

```bash
fapilot runserver
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation. FastAPI also
provides `/redoc` and `/openapi.json`. In a second terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/products/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"Notebook","price_cents":500}'
curl 'http://127.0.0.1:8000/api/products/?limit=10&offset=0'
curl -X PATCH http://127.0.0.1:8000/api/products/1 \
  -H 'Content-Type: application/json' -d '{"price_cents":600}'
curl -X DELETE http://127.0.0.1:8000/api/products/1
```

The first response has HTTP 201 and includes `id`, `name`, and `price_cents`.
The list response has `items`, `total`, `limit`, and `offset`. Deletion returns 204.
A missing product returns 404; invalid request fields return 422.

## Next steps

Add the [integration test](testing.md), learn [configuration precedence](configuration.md),
and move from debug table creation to [managed migrations](databases.md).
Before exposing write endpoints, implement [authentication and permissions](authentication.md).
