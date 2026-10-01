from app.core.exceptions import AppError
from app.providers.local_catalog import LocalBookProvider, normalize
from app.schemas.book import BookSearchResponse


class HybridBookService:
    def __init__(self, external):
        self.external = external
        self.provider = external.provider
        self.local = LocalBookProvider()

    async def search(self, query, limit):
        local = await self.local.search(query, limit)
        try:
            remote = await self.external.search(query, limit)
        except AppError:
            if local.items:
                return local
            raise
        seen, items = set(), []
        for book in [*remote.items, *local.items]:
            key = (normalize(book.title), normalize(" ".join(book.authors)))
            if key not in seen:
                seen.add(key)
                items.append(book)
        return BookSearchResponse(
            items=items[:limit], total=max(len(items), remote.total)
        )

    async def discover(self, query, limit, *, offset=0):
        return await self.external.search(query, limit, discovery=True, offset=offset)

    def get_by_id(self, book_id):
        local = self.local.get_by_id(book_id)
        return local if local else self.external.get_by_id(book_id)
