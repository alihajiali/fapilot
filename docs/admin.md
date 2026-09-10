# Administration

Fapilot includes a server-rendered administration workspace with its own responsive
light/dark design. It uses Tortoise models and works with the default project layout
and all 20 architecture scaffolds. No frontend build, CDN, or additional runtime is needed.

## Enable the panel

Generated projects include `config/admin.py` with a `create_staff_site()` instance.
For existing projects, create it:

```python
# config/admin.py
from fapilot.admin import create_staff_site

site = create_staff_site(title="My workspace")
```

Configure your settings:

```python
ADMIN_ENABLED = True
ADMIN_SITE = "config.admin.site"
ADMIN_URL = "/admin"
ADMIN_MODULES = []
ADMIN_SECURE_COOKIES = True
ADMIN_SESSION_SECONDS = 3600
# Set SECRET_KEY to a private, random value of at least 32 characters.
```

The panel is disabled by default. Use `ADMIN_SECURE_COOKIES=False` only for local
HTTP development. The default is HTTPS-only cookies. There are no default credentials.

Admin users, groups, and history are added to the existing `models` database group.
For a fresh production database, initialize it with `aerich --app models init-db`.
If that group already exists, run `fapilot makemigrations --app models`, review the
migration, and run `fapilot migrate --app models`. `DEBUG=True` creates missing tables
for local development. Then run:

```bash
python manage.py createsuperuser
python manage.py runserver
```

Open `/admin/`. The account creation command prompts for a username, email, and a
confirmed password of at least 12 characters. It does not accept passwords as command
arguments. From a standalone shell command, set `FAPILOT_SETTINGS_MODULE=config.settings`
before running `fapilot createsuperuser`.

## Register models

`fapilot startapp` creates an `admin.py` registration example. The framework discovers
`<installed_app>.admin` modules when the admin is enabled. Imports with broken dependencies
fail visibly; only genuinely absent admin modules are skipped.

```python
# apps.products/admin.py
from fapilot.admin import ModelAdmin, register
from config.admin import site
from .models import Product

@register(Product, site=site, name="products")
class ProductAdmin(ModelAdmin):
    verbose_name = "Products"
    list_display = ("id", "name", "price", "active")
    search_fields = ("name", "description")
    list_filter = ("active",)
    ordering = ("name",)
    list_per_page = 25
    exclude = ("internal_token",)
    readonly_fields = ("sku",)
    fieldsets = (
        ("Product", {"fields": ("name", "sku", "description", "category_id")}),
        ("Availability", {"fields": ("price", "active")}),
    )
    labels = {"category_id": "Category"}
    help_texts = {"price": "Price in USD."}
```

Alternatively, call `site.register(Product, ProductAdmin, name="products")`.
Each site owns its registry. Registering the same model or URL name twice raises an error;
`site.unregister(Product)` removes it. Without an explicit name, the lowercased Python
module path and class name form the URL name. Explicit names keep URLs and permission
strings stable when models move between packages.

## Architecture integration

The same `ModelAdmin` API applies everywhere. Models need to be included in the existing
Tortoise configuration; registering an admin does not register an ORM model or create a
service, broker, or remote database adapter.

| Architecture | Example explicit registration module |
| --- | --- |
| MVC | `controllers.admin` |
| MVVM | `viewmodels.admin` |
| MTV | `views.admin` |
| MVP | `presenters.admin` |
| Layered | `presentation.admin` |
| Clean | `interfaces.admin` |
| Hexagonal | `adapters.inbound.admin` |
| Onion | `infrastructure.admin` |
| Component-based | `pages.admin` |
| Microservices | `services.users.admin` |
| Monolithic | `application.users.admin` |
| Modular monolith | `modules.users.admin` |
| Event-driven | `consumers.admin` |
| CQRS | `commands.admin` |
| Event sourcing | `projections.admin` |
| PAC | `agents.control.admin` |
| HMVC | `modules.main.controllers.admin` |
| VIPER | `routers.admin` |
| Flux | `actions.admin` |
| Redux | `actions.admin` |

Create your selected modules, then list their dotted paths in `ADMIN_MODULES`:

```python
ADMIN_MODULES = ["interfaces.admin", "infrastructure.reporting_admin"]
DATABASE_APPS = {"catalog": {"models": ["infrastructure.models"]}}
```

For clean architecture, CQRS, or event sourcing, override `get_queryset`, `clean`,
`save_model`, and `delete_model` to use the application's service boundaries. The default
save/delete hooks write directly through Tortoise. A custom queryset must retain its
Tortoise-compatible filtering, ordering, pagination, and count interface.

## Available pages and controls

- Login, sign out, password change, and expired-session redirects.
- Dashboard with permission-aware model navigation and record counts.
- Lists with search, exact field filters, sortable database columns, pagination,
  selection checkboxes, and empty states.
- Add/edit/read-only forms with labels, help text, field grouping, server validation,
  JSON/text/date/datetime/number/boolean controls, and model defaults.
- Foreign-key selectors using the underlying ID field (for example `category_id`).
- Many-to-many editing through multi-select controls; reverse relationships are not edited.
- Save, save and continue, and save and add another.
- Single deletion and bulk-operation confirmation pages.
- Selected-record CSV download, custom bulk actions, and bulk deletion.
- Per-record audit history with actor, timestamp, operation, and submitted field names.
- Built-in staff user and group management, with password hashes hidden from forms/exports.
- Themed validation, access-denied, missing-record, and login-throttling states.

Every page uses the same theme. The first visit respects the OS color scheme; the theme
button saves the preference in local storage. Navigation, forms, tables, and dialogs work
without JavaScript; theme switching and select-all use a small local script. Tables scroll
within their container on small screens. The interface includes focus indicators, labels,
a skip link, and status/alert announcements.

## Customization reference

| Option or async hook | Purpose |
| --- | --- |
| `list_display` | Columns; model attributes, model methods, or admin methods accepting an object |
| `search_fields` | Fields combined with case-insensitive OR search |
| `list_filter` | Allowlisted exact-value filters |
| `ordering` | Default Tortoise ordering; database-backed list columns can override it |
| `list_per_page` | Page size, from 1 to 200 |
| `fields` / `fieldsets` | Form field order and grouping; `fields` takes precedence |
| `exclude` | Fields omitted from forms; explicitly choose safe list/export columns separately |
| `readonly_fields` | Displayed form fields ignored in submitted data |
| `password_fields` | Empty password controls; masked list values; excluded from CSV |
| `labels` / `help_texts` | Form labels and supporting descriptions |
| `actions` | Allowed action method names; set `()` to disable |
| `export_fields` | CSV columns; defaults to `list_display`, then the primary key |
| `get_queryset(request)` | Scope all list, count, edit, delete, history, and bulk object lookups |
| `get_list_value(request, obj, name)` | Customize display/export values; HTML is always escaped |
| `get_field_choices(request, name)` | Return allowed `(value, label)` choices or `None` for raw input |
| `clean(request, values, obj)` | Validate/transform scalar values before persistence |
| `save_model(request, obj, change)` | Save through your service layer |
| `delete_model(request, obj)` | Delete through your service layer |
| `has_view_permission(request, obj=None)` | Model and object visibility |
| `has_add_permission(request)` | Creation access |
| `has_change_permission(request, obj=None)` | Editing access; denied objects can be shown read-only |
| `has_delete_permission(request, obj=None)` | Individual and bulk deletion access |
| `has_export_permission(request)` | CSV access; defaults to view access |
| `has_action_permission(request, action)` | Per-action access; custom actions default to change access |

Default relationship selectors fetch up to 201 related objects; at most 200 are shown.
Larger relations use raw IDs (comma-separated for many-to-many). Override
`get_field_choices` for tenant-scoped relationships; returned choices are checked again
on submission. Default related choices use the related model's unrestricted queryset.
Many-to-many updates are performed after `save_model`, inside the write transaction.

Custom validation can raise `ValueError`; forms retain submitted values and show a generic
validation error without exposing database details. Password inputs are always cleared.
Generated primary keys and automatic timestamp fields are omitted. Fields with defaults
use their default on creation when left empty. On edits, empty nullable fields become null.

## Staff users and groups

Only superusers can manage built-in staff users and permission groups. Staff must be active
and have `is_staff=True`. Superusers have full access. Other staff receive model permissions
from their groups, using the registered model URL name:

```json
["products.view", "products.add", "products.change", "products.delete"]
```

Viewing is required before any model endpoint can be used. Grant view alongside other
permissions. CSV defaults to view permission; override its hook for a separate policy.
Custom actions require change access to every selected object. Object permission hooks
run again when the action is confirmed. Use `get_queryset` to scope tenants so dashboard
counts and pagination do not disclose out-of-scope records.

Passwords use salted PBKDF2-SHA256 with 600,000 iterations, computed outside the async event
loop. Password changes invalidate existing sessions at their next request. Every request
rechecks active staff status and current permissions. Superusers cannot delete themselves
or disable their own administrative access through the built-in user admin.

## Bring your own authentication

Use `AdminSite` when your project already has staff identity:

```python
from fapilot.admin import AdminSite

async def authenticate(request, username, password):
    # Verify credentials against your identity provider.
    # Return a stable staff identifier, or None on failure.
    ...

async def authorize(request, identifier):
    # Recheck active staff authorization on EVERY request.
    ...

site = AdminSite(title="Operations", authenticate=authenticate, authorize=authorize)
```

Both callbacks are required to sign in. Plain `AdminSite` fails closed without them.
Callbacks may be sync or async. Authenticated identity is available as
`request.state.admin_user`. Custom backends grant ModelAdmin access by default; override
permission hooks, or populate `request.state.admin_permissions` with the grant strings
above and `request.state.admin_superuser` with a boolean. Set
`request.state.admin_session_version` during authorization to revoke sessions when your
identity provider's credential version changes. An optional
`change_password(request, old_password, new_password)` callback enables that page; return
false or raise `ValueError` when rejected.

For direct FastAPI integration, call
`site.mount(app, secret_key=..., prefix="/admin", secure_cookies=True)` after registration.
You must initialize Tortoise with your models and `fapilot.admin.models` in the `models`
group, and manage their schema. Framework startup performs that configuration automatically.

## Bulk actions

```python
class ProductAdmin(ModelAdmin):
    actions = ("archive", "export_csv", "delete_selected")

    async def archive(self, request, obj):
        obj.active = False
        await obj.save(update_fields=["active"])
```

Custom actions receive each selected, permission-checked object individually. Selection
is explicit and limited to 200 records. Mutations require confirmation and CSRF validation;
export is a CSRF-protected download. CSV cells that could be interpreted as spreadsheet
formulas are prefixed with an apostrophe. No export implicitly includes every model field.

Writes use a transaction on the model's configured connection. On a single database,
model changes and their audit entries roll back together. Admin audit tables live on the
default connection: changes on another connection and their audit records are **not a
distributed transaction**. A cross-database failure may leave audit metadata for rolled-back
changes. External effects from custom hooks (email, services, queues) are also not rolled
back. Use an application outbox or equivalent service transaction design when those effects
must be atomic.

## Operational scope

This is a native Fapilot admin, not a drop-in implementation of every Django admin API.
Nested inline formsets, file uploads/storage, arbitrary non-Tortoise data sources, MFA/SSO
flows, password reset email, and Django template overrides are not built in. Integrate
identity-provider requirements through auth hooks and domain operations through model hooks.
Audit history records admin operations only, not changes made elsewhere. A record's page
shows its latest 100 entries; deletion metadata remains in the audit table.

Sessions are signed, expiring, HttpOnly, SameSite=Strict cookies. Forms use a session-bound
CSRF nonce, including login/logout. HTML is escaped, responses disable caching, and a CSP
blocks framing and remote scripts. Login throttling permits 10 attempts per client address
per five minutes **per process**. For multiple workers or reverse proxies, configure trusted
proxy addresses and shared rate limiting at your gateway. Changing the signing key revokes
all sessions.

## Runnable showcase

From the repository root with Fapilot installed:

```bash
export ADMIN_DEMO_PASSWORD='choose-a-long-demo-password'
uvicorn examples.admin_demo:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/admin/` and log in as `admin`. The showcase includes products,
categories, staff, and groups. It uses an in-memory database and loses changes on restart.

The registration patterns are inspired by the
[Django ModelAdmin reference](https://docs.djangoproject.com/en/dev/ref/contrib/admin/).
Transaction boundaries follow [Tortoise transaction behavior](https://tortoise.github.io/transactions.html).
