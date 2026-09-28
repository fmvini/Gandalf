import asyncio
from collections import OrderedDict
from time import monotonic

from app.core.exceptions import AppError
from app.providers.base import BookProvider
from app.schemas.book import BookSearchResponse


class BookService:
    def __init__(self, provider: BookProvider, cache_ttl_seconds: int = 300) -> None:
        self.provider = provider
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: OrderedDict[tuple[str, int], tuple[float, BookSearchResponse]] = (
            OrderedDict()
        )
        self._lock = asyncio.Lock()

    async def search(self, query: str, limit: int) -> BookSearchResponse:
        title = " ".join(query.split())
        if len(title) < 2:
            raise AppError(
                422,
                "VALIDATION_ERROR",
                "Informe ao menos 2 caracteres para buscar livros.",
            )
        cache_key = (title.casefold(), limit)
        async with self._lock:
            cached = self._cache.get(cache_key)
            if cached and cached[0] > monotonic():
                self._cache.move_to_end(cache_key)
                return cached[1]
            result = await self.provider.search(title, limit)
            if self.cache_ttl_seconds:
                self._cache[cache_key] = (monotonic() + self.cache_ttl_seconds, result)
                self._cache.move_to_end(cache_key)
                if len(self._cache) > 256:
                    self._cache.popitem(last=False)
            return result
