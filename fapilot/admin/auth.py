"""Optional built-in staff accounts, groups and model permissions."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
from typing import ClassVar

from fapilot.admin.models import StaffGroup, StaffUser
from fapilot.admin.options import ModelAdmin
from fapilot.admin.site import AdminSite


def make_password(password: str, *, allow_weak: bool = False) -> str:
    if not password:
        raise ValueError("Password is required")
    if len(password) < 12 and not allow_weak:
        raise ValueError("Use a password with at least 12 characters")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600_000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"


def check_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), int(iterations)
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


async def authenticate(request, username: str, password: str) -> str | None:
    user = await StaffUser.get_or_none(username=username)
    # Run equivalent work for unknown users without blocking the event loop.
    encoded = user.password if user else "pbkdf2_sha256$600000$missing$" + "0" * 64
    valid = await asyncio.to_thread(check_password, password, encoded)
    return str(user.pk) if user and valid and user.is_active and user.is_staff else None


async def authorize(request, identifier: str) -> bool:
    try:
        user = await StaffUser.get_or_none(pk=int(identifier))
    except ValueError:
        return False
    if not user or not user.is_active or not user.is_staff:
        return False
    permissions = set()
    for group in await user.groups.all():
        permissions.update(group.permissions)
    request.state.admin_permissions = permissions
    request.state.admin_superuser = user.is_superuser
    request.state.admin_staff = user
    request.state.admin_session_version = hashlib.sha256(user.password.encode()).hexdigest()
    return True


async def change_password(request, old: str, new: str) -> bool:
    user = request.state.admin_staff
    if not await asyncio.to_thread(check_password, old, user.password):
        return False
    user.password = await asyncio.to_thread(make_password, new)
    await user.save(update_fields=["password"])
    return True


class StaffOnlyAdmin(ModelAdmin):
    async def has_view_permission(self, request, obj=None):
        return bool(getattr(request.state, "admin_superuser", False))

    async def has_add_permission(self, request):
        return await self.has_view_permission(request)

    async def has_change_permission(self, request, obj=None):
        return await self.has_view_permission(request, obj)

    async def has_delete_permission(self, request, obj=None):
        return await self.has_view_permission(request, obj)


class StaffUserAdmin(StaffOnlyAdmin):
    verbose_name = "Staff users"
    list_display = ("id", "username", "email", "is_active", "is_superuser")
    search_fields = ("username", "email")
    list_filter = ("is_active", "is_superuser")
    password_fields = ("password",)
    fieldsets = (
        ("Account", {"fields": ("username", "email", "password")}),
        ("Access", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
    )
    help_texts: ClassVar[dict[str, str]] = {
        "password": "At least 12 characters. Leave blank to keep the current password."
    }

    async def clean(self, request, values, obj):
        password = values.pop("password", "")
        if password:
            values["password"] = await asyncio.to_thread(make_password, password)
        elif obj is None:
            raise ValueError("Password is required")
        if obj is not None and str(obj.pk) == request.state.admin_user:
            if not all(
                values.get(name, True) for name in ("is_active", "is_staff", "is_superuser")
            ):
                raise ValueError("You cannot remove your own administrative access")
        return values

    async def has_delete_permission(self, request, obj=None):
        return await super().has_delete_permission(request, obj) and (
            obj is None or str(obj.pk) != request.state.admin_user
        )


class StaffGroupAdmin(StaffOnlyAdmin):
    verbose_name = "Staff groups"
    list_display = ("id", "name")
    search_fields = ("name",)
    fields = ("name", "permissions")
    help_texts: ClassVar[dict[str, str]] = {
        "permissions": 'JSON list: ["articles.view", "articles.add", "articles.change"].'
    }

    async def clean(self, request, values, obj):
        permissions = values.get("permissions", [])
        if not isinstance(permissions, list) or any(not isinstance(p, str) for p in permissions):
            raise ValueError("Permissions must be a list of strings")
        return values


def create_staff_site(*, title: str = "Fapilot") -> AdminSite:
    site = AdminSite(
        title=title, authenticate=authenticate, authorize=authorize, change_password=change_password
    )
    site.register(StaffUser, StaffUserAdmin, name="staff-users")
    site.register(StaffGroup, StaffGroupAdmin, name="staff-groups")
    return site
