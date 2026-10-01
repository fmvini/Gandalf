from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlaylistCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    source_recommendation_id: UUID | None = None
    music_ids: list[UUID] | None = Field(default=None, min_length=1, max_length=60)

    @model_validator(mode="after")
    def valid_tracks(self):
        if self.source_recommendation_id is None and self.music_ids is None:
            raise ValueError("Informe as músicas ou uma trilha de leitura.")
        if self.music_ids and len(set(self.music_ids)) != len(self.music_ids):
            raise ValueError("A playlist não pode repetir músicas.")
        if (
            self.source_recommendation_id is None
            and self.music_ids
            and len(self.music_ids) > 25
        ):
            raise ValueError("Escolha até 25 músicas para uma playlist manual.")
        return self


class PlaylistSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    source: Literal["MANUAL", "READ_WITH_MUSIC"]
    source_recommendation_id: UUID | None
    total_duration_ms: int
    duration_estimated: bool
    tracks_count: int
    created_at: datetime
    updated_at: datetime


class PlaylistTrackResponse(BaseModel):
    position: int
    item: dict


class PlaylistDetail(PlaylistSummary):
    tracks: list[PlaylistTrackResponse]


class PlaylistList(BaseModel):
    items: list[PlaylistSummary]
    total: int
    limit: int
    offset: int
