from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MusicFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vocals: Literal["none", "required", "optional"] | None = None
    energy: Literal["low", "medium", "high"] | None = None
    excluded_energy: list[Literal["low", "medium", "high"]] = Field(
        default_factory=list, max_length=3
    )

    @model_validator(mode="after")
    def consistent_energy(self):
        if self.energy in self.excluded_energy:
            raise ValueError("O nível de energia não pode ser solicitado e excluído.")
        return self


class DiscoveryRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(min_length=3, max_length=1000)
    filters: MusicFilters = Field(default_factory=MusicFilters)
    limit: int = Field(default=10, ge=1, le=25)


class BookDiscoveryRequest(DiscoveryRequest):
    excluded_book_ids: list[UUID] = Field(default_factory=list, max_length=200)
    offset: int = Field(default=0, ge=0, le=300)


class MusicDiscoveryRequest(DiscoveryRequest):
    excluded_music_ids: list[UUID] = Field(default_factory=list, max_length=200)
    offset: int = Field(default=0, ge=0, le=300)


class ReadingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    book_id: UUID
    mode: Literal["FOCUS", "IMMERSIVE", "CINEMATIC", "CALM", "CUSTOM"] = "FOCUS"
    context: str = Field(default="", max_length=500)
    vocals: Literal["INSTRUMENTAL", "MINIMAL", "ANY"] = "INSTRUMENTAL"
    target_duration_min: int = Field(default=60, ge=15, le=120)

    @model_validator(mode="after")
    def custom_needs_context(self):
        if self.mode == "CUSTOM" and not self.context:
            raise ValueError("Descreva a atmosfera para o modo personalizado.")
        return self
