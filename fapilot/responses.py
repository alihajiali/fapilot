from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def ok(data: Any = None, *, status_code: int = 200) -> JSONResponse:
    return JSONResponse({"data": data}, status_code=status_code)

