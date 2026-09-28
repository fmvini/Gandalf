from uuid import UUID

from pydantic import BaseModel, Field


class BookItem(BaseModel):
    id: UUID
    title: str
    authors: list[str] = Field(default_factory=list)
    description: str | None = None
    genres: list[str] = Field(default_factory=list)
    subjects: list[str] = Field(default_factory=list)
    publication_year: int | None = None
    cover_url: str | None = None
    external_url: str
    provider: str = "open_library"
    external_id: str


class BookSearchResponse(BaseModel):
    items: list[BookItem]
    total: int = Field(ge=0)
