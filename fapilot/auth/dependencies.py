from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.security import SecurityScopes

from fapilot.auth.backends import (
    AuthenticationBackend,
    AuthenticationResult,
    import_callable,
    validate_result,
)
from fapilot.conf import FapilotSettings


class AuthenticationManager:
    def __init__(self, settings: FapilotSettings) -> None:
        self.backends: list[AuthenticationBackend] = []
        for entry in settings.AUTHENTICATION_BACKENDS:
            path = entry if isinstance(entry, str) else entry.backend
            options = {} if isinstance(entry, str) else entry.options
            backend = import_callable(path)(settings=settings, **options)
            if not isinstance(backend, AuthenticationBackend):
                raise TypeError(f"{path} must extend AuthenticationBackend")
            self.backends.append(backend)

    async def authenticate(self, request: Request) -> AuthenticationResult | None:
        if hasattr(request.state, "_fapilot_auth_result"):
            return request.state._fapilot_auth_result
        result = None
        for backend in self.backends:
            result = await backend.authenticate(request)
            if result is not None:
                result = validate_result(result, backend.challenge)
                break
        request.state._fapilot_auth_result = result
        request.state.user = result.user if result else None
        request.state.auth = result
        return result

    @property
    def challenge(self) -> str:
        return ", ".join(dict.fromkeys(b.challenge for b in self.backends)) or "Bearer"


def get_manager(request: Request) -> AuthenticationManager:
    manager = getattr(request.app.state, "authentication", None)
    if manager is None:
        raise RuntimeError("Install AuthenticationManager on app.state.authentication")
    return manager


async def optional_user(request: Request) -> Any:
    """Allow absent credentials; reject supplied invalid credentials."""
    result = await get_manager(request).authenticate(request)
    return result.user if result else None


async def get_current_user(request: Request, security_scopes: SecurityScopes) -> Any:
    manager = get_manager(request)
    result = await manager.authenticate(request)
    if result is None:
        raise HTTPException(
            401, "Authentication required", headers={"WWW-Authenticate": manager.challenge}
        )
    if not set(security_scopes.scopes).issubset(result.scopes):
        raise HTTPException(403, "Insufficient permissions")
    return result.user
