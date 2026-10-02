from typing import Literal, NotRequired, Protocol, TypedDict

from app.schemas.book import BookSearchResponse


class BookProvider(Protocol):
    name: str

    async def search(self, title: str, limit: int) -> BookSearchResponse: ...


class MusicItem(TypedDict):
    """Normalized source metadata; unknown attributes remain None, never guesses."""

    id: str
    title: str
    artist: str
    tags: list[str]
    duration_ms: int | None
    has_vocals: bool | None
    energy: Literal["low", "medium", "high"] | None
    provider: str
    external_id: str
    links: dict[str, str]
    classification_source: NotRequired[Literal["provider_tags", "ai_estimate"]]


class MusicSearchResult(TypedDict):
    items: list[MusicItem]
    total: int
    provider: str
    has_more: bool


class MusicProvider(Protocol):
    """Caller-owned adapter for an external catalog, with no detail API promise.

    Items and results identify this name. IDs are canonical UUIDs, stable in a
    source/external-id namespace; existing MusicBrainz UUID5 URLs are preserved.
    The adapter owns normalization, cache and OnlineStore persistence when
    catalog detail lookup is required. Known metadata is not an acoustic measure.
    """

    name: str

    async def search(
        self,
        query: str,
        limit: int = 20,
        *,
        by_tag: bool = False,
        offset: int = 0,
        reading: bool = False,
        instrumental: bool = False,
    ) -> MusicSearchResult: ...
