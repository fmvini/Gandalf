from typing import Protocol

from app.schemas.book import BookSearchResponse


class BookProvider(Protocol):
    name: str

    async def search(self, title: str, limit: int) -> BookSearchResponse: ...
