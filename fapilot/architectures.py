"""Project architecture scaffold definitions.

These layouts organize application code; they do not install architecture-specific runtimes.
"""

ARCHITECTURES: dict[str, tuple[str, ...]] = {
    "mvc": ("models", "views", "controllers"),
    "mvvm": ("models", "views", "viewmodels"),
    "mtv": ("models", "templates", "views"),
    "mvp": ("models", "views", "presenters"),
    "layered": ("presentation", "business/services", "data_access", "database"),
    "clean": ("entities", "use_cases", "interfaces", "infrastructure"),
    "hexagonal": ("core/domain", "core/ports", "adapters/inbound", "adapters/outbound"),
    "onion": ("domain", "application", "infrastructure"),
    "component-based": ("components", "pages", "layouts", "state"),
    "microservices": ("services/users", "services/orders", "services/payments", "shared"),
    "monolithic": ("application/users", "application/products", "application/orders"),
    "modular-monolith": ("modules/users", "modules/orders", "modules/payments", "shared"),
    "event-driven": ("events", "producers", "consumers", "event_bus"),
    "cqrs": ("commands", "queries", "write_model", "read_model"),
    "event-sourcing": ("events", "event_store", "aggregates", "projections"),
    "pac": ("agents/presentation", "agents/abstraction", "agents/control"),
    "hmvc": ("modules/main/models", "modules/main/views", "modules/main/controllers"),
    "viper": ("views", "interactors", "presenters", "entities", "routers"),
    "flux": ("actions", "dispatcher", "stores", "views"),
    "redux": ("actions", "reducers", "store", "selectors", "views"),
}

ARCHITECTURE_GUIDANCE: dict[str, str] = {
    "mvc": "Controllers coordinate requests, models hold data, and views present results.",
    "mvvm": "View models expose model data and behavior to views.",
    "mtv": "Models hold data, templates render UI, and views handle requests and business logic.",
    "mvp": "Presenters coordinate models and views; keep presentation logic in presenters.",
    "layered": "Presentation calls business services, which use data access and the database.",
    "clean": "Keep entities and use cases independent of interfaces and infrastructure.",
    "hexagonal": "Define ports in the core and implement external integrations in adapters.",
    "onion": "Dependencies point inward from infrastructure through application to domain.",
    "component-based": "Compose pages and layouts from reusable components; isolate shared state.",
    "microservices": "Organize service boundaries independently; add deployment and transport setup.",
    "monolithic": "Run feature areas together as one application.",
    "modular-monolith": "Run one application with explicit interfaces between feature modules.",
    "event-driven": "Producers publish events through the event bus to consumers.",
    "cqrs": "Commands change the write model; queries read from the read model.",
    "event-sourcing": "Persist events in the event store and rebuild state using projections.",
    "pac": "Organize agents into presentation, abstraction, and control responsibilities.",
    "hmvc": "Give each module its own models, views, and controllers.",
    "viper": "Separate UI, use cases, presentation, entities, and navigation routing.",
    "flux": "Actions flow through the dispatcher to stores, then to views.",
    "redux": "Actions feed reducers that update store state; selectors expose state to views.",
}
