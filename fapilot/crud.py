from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from tortoise.models import Model

ModelT = TypeVar("ModelT", bound=Model)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)


class CRUDRouterService(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
    ):
        queryset = self.model.filter(**(filters or {}))
        return await queryset.offset(offset).limit(limit)

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        return await self.model.filter(**(filters or {})).count()

    async def get(self, object_id: Any) -> ModelT | None:
        return await self.model.get_or_none(id=object_id)

    async def create(self, data: CreateSchemaT) -> ModelT:
        return await self.model.create(**data.model_dump())

    async def update(self, instance: ModelT, data: UpdateSchemaT) -> ModelT:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, key, value)
        await instance.save()
        return instance

    async def delete(self, instance: ModelT) -> None:
        await instance.delete()
