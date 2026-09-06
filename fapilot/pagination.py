from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel

from fapilot.conf import get_settings

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    limit: int
    offset: int


class LimitOffset(BaseModel):
    limit: int
    offset: int


def pagination_params(
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
) -> LimitOffset:
    settings = get_settings()
    chosen_limit = limit or settings.DEFAULT_PAGE_SIZE
    return LimitOffset(limit=min(chosen_limit, settings.MAX_PAGE_SIZE), offset=offset)


Pagination = Depends(pagination_params)
