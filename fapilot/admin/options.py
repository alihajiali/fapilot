"""Architecture-independent model administration hooks."""

from __future__ import annotations

from typing import Any, ClassVar

from starlette.requests import Request
from tortoise.models import Model


class ModelAdmin:
    """Subclass to customize presentation, authorization, queries and persistence.

    Every hook is async so service layers and remote authorization can be used.
    Querysets must retain Tortoise's queryset interface.
    """

    list_display: tuple[str, ...] = ()
    search_fields: tuple[str, ...] = ()
    list_filter: tuple[str, ...] = ()
    ordering: tuple[str, ...] = ()
    fields: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    readonly_fields: tuple[str, ...] = ()
    password_fields: tuple[str, ...] = ()
    registry_name: str = ""
    list_per_page: int = 25
    verbose_name: str | None = None
    icon: str = "box"
    description: str = ""
    menu_group: str = "Collections"
    fieldsets: tuple[tuple[str, dict[str, Any]], ...] = ()
    actions: tuple[str, ...] = ("delete_selected", "export_csv")
    export_fields: tuple[str, ...] = ()
    help_texts: ClassVar[dict[str, str]] = {}
    labels: ClassVar[dict[str, str]] = {}

    async def has_export_permission(self, request: Request) -> bool:
        return await self.has_view_permission(request)

    async def has_action_permission(self, request: Request, action: str) -> bool:
        if action == "export_csv":
            return await self.has_export_permission(request)
        if action == "delete_selected":
            return await self.has_delete_permission(request)
        return await self.has_change_permission(request)

    async def clean(self, request: Request, values: dict[str, Any], obj: Model | None) -> dict:
        """Validate/transform form values; raise ValueError to reject the submission."""
        return values

    async def get_field_choices(self, request: Request, name: str) -> list[tuple[Any, str]] | None:
        """Override for scoped foreign-key choices or custom select fields."""
        field = self.model._meta.fields_map[name]
        reference = (
            field if name in self.model._meta.m2m_fields else getattr(field, "reference", None)
        )
        related_model = getattr(reference, "related_model", None)
        if related_model is not None:
            # Raw ID input is used for large relations; applications may override this hook.
            objects = await related_model.all().limit(201)
            if len(objects) <= 200:
                target = getattr(reference, "to_field", None) or related_model._meta.pk_attr
                return [(getattr(obj, target), str(obj)) for obj in objects]
        return None

    async def get_list_value(self, request: Request, obj: Model, name: str) -> Any:
        import inspect

        value = getattr(self, name, None)
        if callable(value):
            value = value(obj)
        else:
            value = getattr(obj, name, "")
            if callable(value):
                value = value()
        return await value if inspect.isawaitable(value) else value

    def __init__(self, model: type[Model]) -> None:
        self.model = model
        if not 1 <= self.list_per_page <= 200:
            raise ValueError("list_per_page must be between 1 and 200")

    async def has_view_permission(self, request: Request, obj: Model | None = None) -> bool:
        return self._permission(request, "view")

    async def has_add_permission(self, request: Request) -> bool:
        return self._permission(request, "add")

    async def has_change_permission(self, request: Request, obj: Model | None = None) -> bool:
        return self._permission(request, "change")

    async def has_delete_permission(self, request: Request, obj: Model | None = None) -> bool:
        return self._permission(request, "delete")

    async def get_queryset(self, request: Request) -> Any:
        return self.model.all()

    async def save_model(self, request: Request, obj: Model, change: bool) -> None:
        await obj.save()

    async def delete_model(self, request: Request, obj: Model) -> None:
        await obj.delete()

    def _permission(self, request: Request, action: str) -> bool:
        grants = getattr(request.state, "admin_permissions", None)
        return (
            grants is None
            or getattr(request.state, "admin_superuser", False)
            or (f"{self.registry_name}.{action}" in grants)
        )

    def get_fields(self, change: bool = False) -> list[str]:
        meta = self.model._meta
        names = (
            self.fields
            or tuple(name for _, options in self.fieldsets for name in options["fields"])
            or (*meta.fields_db_projection, *sorted(meta.m2m_fields))
        )
        return [
            name
            for name in names
            if name not in self.exclude
            and (name in meta.fields_db_projection or name in meta.m2m_fields)
            and not (meta.fields_map[name].pk and (change or meta.fields_map[name].generated))
            and not getattr(meta.fields_map[name], "auto_now", False)
            and not getattr(meta.fields_map[name], "auto_now_add", False)
        ]
