from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from fapilot.conf import get_settings


def create_access_token(subject: str, claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    jwt_settings = settings.JWT_SETTINGS
    expires_at = datetime.now(UTC) + timedelta(minutes=jwt_settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "iss": jwt_settings.issuer,
        "exp": expires_at,
        **(claims or {}),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=jwt_settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_SETTINGS.algorithm])
    except JWTError:
        return None

