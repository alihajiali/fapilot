# Project layout and architectures

[Documentation index](index.md)

## Shared generated layout

```text
myproject/
├── config/             settings, ORM config, ASGI entry point, routing placeholder
├── apps/               feature apps created with startapp
├── common/             imports of framework helpers and shared-code placeholders
├── tests/
├── manage.py
├── .env
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

| File | Purpose and runtime behavior |
| --- | --- |
| `config/settings.py` | Uppercase settings read by `load_settings` |
| `config/database.py` | Builds `TORTOISE_ORM` for Aerich from settings and the registry |
| `config/asgi.py` | Exposes `app`, sets the settings-module environment default |
| `config/urls.py` | Empty `APIRouter`; not automatically included in the app |
| `config/logging.py` | Empty logging dictionary; not automatically applied |
| `manage.py` | Calls the same `main()` function as the `fapilot` command |
| `common/*.py` | Re-exports and placeholders; no automatic middleware/model discovery |
| `pyproject.toml` | Project name/version, Fapilot dependency, Aerich configuration |
| `Dockerfile` | Basic Python/Uvicorn image; installs unpinned Fapilot |
| `docker-compose.yml` | PostgreSQL service only; does not run or configure the application |

Generated `common/` files are `crud`, `pagination`, `filtering`, `exceptions`,
`permissions`, `middleware`, `responses`, `events`, `models`, `schemas`, and `utils`.
Do not assume a placeholder activates a framework feature.

## Generated feature app

`fapilot startapp users` creates `apps/users/` with:

| File | Intended responsibility |
| --- | --- |
| `apps.py` | `UsersConfig(AppConfig)` with name `apps.users` and label `users` |
| `models.py` | Tortoise models, discovered when the app is registered |
| `api.py` | FastAPI router, discovered when the app is registered |
| `schemas.py` | Pydantic request and response schemas |
| `services.py`, `repositories.py` | Business logic and database access conventions |
| `permissions.py`, `dependencies.py` | Application permission/dependency code |
| `signals.py` | Signal receivers; import/connect them explicitly |
| `admin.py` | Placeholder only; no admin site is supplied |
| `tests/`, `migrations/` | Python packages; Aerich's default migration location is elsewhere |

Register `"apps.users.apps.UsersConfig"` in `INSTALLED_APPS` after generation.
Use simple Python identifiers for app names, such as `users` or `order_items`.
The CLI does not validate Python identifiers or normalize nested app names.
Existing destination directories cause an error instead of being overwritten.

## Select an architecture

```bash
fapilot startproject myproject --architecture clean
# Equivalent option name:
fapilot startproject anotherproject --structure clean
```

The option accepts one lowercase slug. Without it, only the shared layout is generated.
All choices keep that layout and add the folders below. Nested directories get
`__init__.py`; a directory named `templates` remains a plain directory.

| Slug | Architecture | Additional folders |
| --- | --- | --- |
| `mvc` | Model View Controller | `models/`, `views/`, `controllers/` |
| `mvvm` | Model View ViewModel | `models/`, `views/`, `viewmodels/` |
| `mtv` | Model Template View | `models/`, `templates/`, `views/` |
| `mvp` | Model View Presenter | `models/`, `views/`, `presenters/` |
| `layered` | Layered / N-tier | `presentation/`, `business/services/`, `data_access/`, `database/` |
| `clean` | Clean | `entities/`, `use_cases/`, `interfaces/`, `infrastructure/` |
| `hexagonal` | Hexagonal / Ports and Adapters | `core/domain/`, `core/ports/`, `adapters/inbound/`, `adapters/outbound/` |
| `onion` | Onion | `domain/`, `application/`, `infrastructure/` |
| `component-based` | Component-Based | `components/`, `pages/`, `layouts/`, `state/` |
| `microservices` | Microservices | `services/users/`, `services/orders/`, `services/payments/`, `shared/` |
| `monolithic` | Monolithic | `application/users/`, `application/products/`, `application/orders/` |
| `modular-monolith` | Modular Monolith | `modules/users/`, `modules/orders/`, `modules/payments/`, `shared/` |
| `event-driven` | Event-Driven | `events/`, `producers/`, `consumers/`, `event_bus/` |
| `cqrs` | Command Query Responsibility Segregation | `commands/`, `queries/`, `write_model/`, `read_model/` |
| `event-sourcing` | Event Sourcing | `events/`, `event_store/`, `aggregates/`, `projections/` |
| `pac` | Presentation Abstraction Control | `agents/presentation/`, `agents/abstraction/`, `agents/control/` |
| `hmvc` | Hierarchical MVC | `modules/main/models/`, `modules/main/views/`, `modules/main/controllers/` |
| `viper` | View Interactor Presenter Entity Router | `views/`, `interactors/`, `presenters/`, `entities/`, `routers/` |
| `flux` | Flux | `actions/`, `dispatcher/`, `stores/`, `views/` |
| `redux` | Redux | `actions/`, `reducers/`, `store/`, `selectors/`, `views/` |

## Responsibilities and integration

- **mvc:** Controllers coordinate requests, models hold data, and views present results.
- **mvvm:** View models expose model data and behavior to views.
- **mtv:** Models hold data, templates render UI, and views handle requests and business logic.
- **mvp:** Presenters coordinate models and views; keep presentation logic in presenters.
- **layered:** Presentation calls business services, which use data access and the database.
- **clean:** Keep entities and use cases independent of interfaces and infrastructure.
- **hexagonal:** Define ports in the core and implement external integrations in adapters.
- **onion:** Dependencies point inward from infrastructure through application to domain.
- **component-based:** Compose pages and layouts from reusable components; isolate shared state.
- **microservices:** Organize service boundaries independently; add deployment and transport setup.
- **monolithic:** Run feature areas together as one application.
- **modular-monolith:** Run one application with explicit interfaces between feature modules.
- **event-driven:** Producers publish events through the event bus to consumers.
- **cqrs:** Commands change the write model; queries read from the read model.
- **event-sourcing:** Persist events in the event store and rebuild state using projections.
- **pac:** Organize agents into presentation, abstraction, and control responsibilities.
- **hmvc:** Give each module its own models, views, and controllers.
- **viper:** Separate UI, use cases, presentation, entities, and navigation routing.
- **flux:** Actions flow through the dispatcher to stores, then to views.
- **redux:** Actions feed reducers that update store state; selectors expose state to views.

These selections create empty organizational scaffolds and README guidance. They do
not enforce dependency directions, move generated apps, create model implementations,
or install React, Redux, Django, brokers, or service deployments. `startapp` always
uses the same app template. There is no command to switch an existing project layout.

For a clean architecture project, an app's `api.py` can call code in `use_cases/`,
which works with entities and interfaces implemented by `infrastructure/`.
Register routers through `AppConfig` and model modules through `DATABASE_APPS` or
`tortoise_models`; architecture directories are not scanned automatically.
