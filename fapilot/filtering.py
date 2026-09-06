from __future__ import annotations

from typing import Any


def pick_filters(params: dict[str, Any], allowed: set[str]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if key in allowed and value is not None}

