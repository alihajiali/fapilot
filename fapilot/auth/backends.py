"""Composable async API authentication with application-owned identity storage."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass, field
from importlib import import_module
from typing import Any

from fastapi import HTTPException, Request

from fapilot.auth.jwt import decode_access_token
from fapilot.conf import FapilotSettings


@dataclass(frozen=True)
class AuthenticationResult:
    user: Any
    scopes: frozenset[str] = field(default_factory=frozenset)
    claims: dict[str, Any] = field(default_factory=dict)


class AuthenticationError(HTTPException):
    def __init__(self, challenge: str = "Bearer") -> None:
        super().__init__(
            401, "Invalid authentication credentials", headers={"WWW-Authenticate": challenge}
        )


def import_callable(path: str) -> Any:
    module, _, name = path.rpartition(".")
    if not module:
        raise ValueError(f"Expected a dotted import path, got {path!r}")
    value = getattr(import_module(module), name)
    if not callable(value):
        raise ValueError(f"{path!r} is not callable")
    return value


class AuthenticationBackend:
    """Return None only for absent/not-applicable credentials; raise on rejection.

    Instances are shared across requests. Keep request data in local variables.
    """

    challenge = "Bearer"

    def __init__(self, settings: FapilotSettings) -> None:
        self.settings = settings

    async def authenticate(self, request: Request) -> AuthenticationResult | None:
        raise NotImplementedError


def authorization(request: Request, scheme: str) -> str | None:
    values = request.headers.getlist("authorization")
    if len(values) > 1:
        raise AuthenticationError(scheme)
    if not values:
        return None
    parts = values[0].split()
    if not parts or parts[0].lower() != scheme.lower():
        return None
    if len(parts) != 2:
        raise AuthenticationError(scheme)
    return parts[1]


class JWTBackend(AuthenticationBackend):
    def __init__(self, settings: FapilotSettings, user_loader: str | None = None) -> None:
        super().__init__(settings)
        self.user_loader = import_callable(user_loader) if user_loader else None
        if settings.SECRET_KEY == "change-me" and not settings.JWT_SETTINGS.verification_key:
            raise ValueError("JWTBackend requires a configured SECRET_KEY or verification_key")

    async def authenticate(self, request: Request) -> AuthenticationResult | None:
        token = authorization(request, "Bearer")
        if token is None:
            return None
        claims = decode_access_token(token, settings=self.settings)
        if claims is None:
            raise AuthenticationError()
        user = await self.user_loader(request, claims) if self.user_loader else claims["sub"]
        if user is None or getattr(user, "is_active", True) is False:
            raise AuthenticationError()
        scope = claims.get("scope", "")
        if not isinstance(scope, str):
            raise AuthenticationError()
        return AuthenticationResult(user, frozenset(scope.split()), claims)


class BasicBackend(AuthenticationBackend):
    challenge = 'Basic realm="api", charset="UTF-8"'

    def __init__(self, settings: FapilotSettings, verifier: str) -> None:
        super().__init__(settings)
        self.verifier = import_callable(verifier)

    async def authenticate(self, request: Request) -> AuthenticationResult | None:
        token = authorization(request, "Basic")
        if token is None:
            return None
        try:
            username, password = (
                base64.b64decode(token, validate=True).decode("utf-8").split(":", 1)
            )
        except (ValueError, UnicodeError, binascii.Error):
            raise AuthenticationError(self.challenge) from None
        result = await self.verifier(request, username, password)
        return validate_result(result, self.challenge)


def validate_result(result: Any, challenge: str) -> AuthenticationResult:
    if result is None:
        raise AuthenticationError(challenge)
    if not isinstance(result, AuthenticationResult):
        raise TypeError("Authentication verifiers must return AuthenticationResult or None")
    if result.user is None or getattr(result.user, "is_active", True) is False:
        raise AuthenticationError(challenge)
    return result


class TokenBackend(AuthenticationBackend):
    """Validate opaque bearer tokens through an async verifier (e.g. OAuth introspection)."""

    def __init__(self, settings: FapilotSettings, verifier: str, scheme: str = "Bearer") -> None:
        super().__init__(settings)
        if not scheme.isascii() or not scheme.isalnum():
            raise ValueError("Token scheme must be ASCII alphanumeric")
        self.challenge = scheme
        self.verifier = import_callable(verifier)

    async def authenticate(self, request: Request) -> AuthenticationResult | None:
        token = authorization(request, self.challenge)
        if token is None:
            return None
        return validate_result(await self.verifier(request, token), self.challenge)


class APIKeyBackend(AuthenticationBackend):
    challenge = "ApiKey"

    def __init__(self, settings: FapilotSettings, verifier: str, header: str = "X-API-Key") -> None:
        super().__init__(settings)
        if not header or any(c.isspace() for c in header):
            raise ValueError("API key header must be nonempty and contain no whitespace")
        self.header = header
        self.verifier = import_callable(verifier)

    async def authenticate(self, request: Request) -> AuthenticationResult | None:
        values = request.headers.getlist(self.header)
        if not values:
            return None
        if len(values) != 1 or not values[0].strip():
            raise AuthenticationError(self.challenge)
        return validate_result(await self.verifier(request, values[0]), self.challenge)
