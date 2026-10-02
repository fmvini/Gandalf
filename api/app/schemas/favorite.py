from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

FavoriteType = Literal["MUSIC", "BOOK"]


class FavoriteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_id: UUID
    item_id: UUID


class FavoriteResponse(BaseModel):
    id: UUID
    type: FavoriteType
    item_id: UUID
    item: dict
    created_at: datetime


class FavoriteList(BaseModel):
    items: list[FavoriteResponse]
    total: int
    limit: int
    offset: int


class FavoriteStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: FavoriteType
    item_ids: list[UUID] = Field(min_length=1, max_length=60)

    @model_validator(mode="after")
    def unique_items(self):
        if len(set(self.item_ids)) != len(self.item_ids):
            raise ValueError("Informe IDs de itens únicos.")
        return self


class FavoriteStatus(BaseModel):
    favorites: dict[UUID, UUID]
