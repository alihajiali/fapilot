from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from fapilot.conf import FapilotSettings, get_settings


def create_access_token(
    subject: str,
    claims: dict[str, Any] | None = None,
    *,
    settings: FapilotSettings | None = None,
) -> str:
    settings = settings or get_settings()
    if settings.SECRET_KEY == "change-me":
        raise ValueError("Configure SECRET_KEY before issuing tokens")
    if not subject:
        raise ValueError("Token subject must not be empty")
    if {"sub", "iss", "exp", "aud"}.intersection(claims or {}):
        raise ValueError("Reserved JWT claims cannot be overridden")
    jwt_settings = settings.JWT_SETTINGS
    expires_at = datetime.now(UTC) + timedelta(minutes=jwt_settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "iss": jwt_settings.issuer,
        "exp": expires_at,
        **(claims or {}),
    }
    if jwt_settings.audience is not None:
        payload["aud"] = jwt_settings.audience
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=jwt_settings.algorithm)


def decode_access_token(
    token: str,
    *,
    settings: FapilotSettings | None = None,
) -> dict[str, Any] | None:
    settings = settings or get_settings()
    config = settings.JWT_SETTINGS
    key = config.verification_key or settings.SECRET_KEY
    if key == "change-me":
        return None
    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[config.algorithm],
            issuer=config.issuer,
            audience=config.audience,
            options={
                "require_exp": True,
                "require_sub": True,
                "require_iss": True,
                "require_aud": config.audience is not None,
                "leeway": config.leeway,
            },
        )
        return claims if isinstance(claims.get("sub"), str) and claims["sub"] else None
    except (JWTError, TypeError, ValueError, OverflowError):
        return None
