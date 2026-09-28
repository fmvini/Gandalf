from typing import Protocol

from app.schemas.book import BookSearchResponse


class BookProvider(Protocol):
    async def search(self, title: str, limit: int) -> BookSearchResponse: ...
