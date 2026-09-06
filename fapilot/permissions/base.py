from __future__ import annotations

from typing import Protocol

from fastapi import HTTPException, Request, status


class Permission(Protocol):
    async def has_permission(self, request: Request) -> bool: ...


class AllowAny:
    async def has_permission(self, request: Request) -> bool:
        return True


class IsAuthenticated:
    async def has_permission(self, request: Request) -> bool:
        return getattr(request.state, "user", None) is not None


async def require_permissions(request: Request, *permissions: Permission) -> None:
    for permission in permissions:
        if not await permission.has_permission(request):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

