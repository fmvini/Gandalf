import asyncio
from collections import OrderedDict
from time import monotonic
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import AppError
from app.models.book import Book
from app.providers.base import BookProvider
from app.schemas.book import BookItem, BookSearchResponse


class BookService:
    def __init__(
        self,
        provider: BookProvider,
        cache_ttl_seconds: int = 300,
        session_factory: sessionmaker[Session] | None = None,
    ) -> None:
        self.provider = provider
        self.cache_ttl_seconds = cache_ttl_seconds
        self.session_factory = session_factory
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
            if self.session_factory is not None:
                result = await run_in_threadpool(self._persist, result)
            if self.cache_ttl_seconds:
                self._cache[cache_key] = (monotonic() + self.cache_ttl_seconds, result)
                self._cache.move_to_end(cache_key)
                if len(self._cache) > 256:
                    self._cache.popitem(last=False)
            return result

    def get_by_id(self, book_id: UUID) -> BookItem:
        if self.session_factory is None:
            raise AppError(
                503, "SERVICE_UNAVAILABLE", "O catálogo de livros não está configurado."
            )
        try:
            with self.session_factory() as session:
                record = session.get(Book, book_id)
                if record is None:
                    raise AppError(404, "NOT_FOUND", "Livro não encontrado.")
                return self._to_item(record)
        except SQLAlchemyError as exc:
            raise AppError(
                503, "SERVICE_UNAVAILABLE", "O catálogo de livros está indisponível."
            ) from exc

    def _persist(self, result: BookSearchResponse) -> BookSearchResponse:
        assert self.session_factory is not None
        try:
            with self.session_factory() as session:
                for item in result.items:
                    values = {
                        "title": item.title,
                        "authors": item.authors,
                        "description": item.description,
                        "genres": item.genres,
                        "subjects": item.subjects,
                        "publication_year": item.publication_year,
                        "cover_url": item.cover_url,
                        "external_url": item.external_url,
                    }
                    update_values = {**values, "updated_at": func.now()}
                    dialect = session.get_bind().dialect.name
                    if dialect == "postgresql":
                        statement = pg_insert(Book).values(
                            id=item.id,
                            provider=item.provider,
                            external_id=item.external_id,
                            metadata_json={},
                            **values,
                        )
                        statement = statement.on_conflict_do_update(
                            constraint="uq_books_provider_external",
                            set_=update_values,
                        )
                        session.execute(statement)
                    elif dialect == "sqlite":
                        statement = sqlite_insert(Book).values(
                            id=item.id,
                            provider=item.provider,
                            external_id=item.external_id,
                            metadata_json={},
                            **values,
                        )
                        statement = statement.on_conflict_do_update(
                            index_elements=[Book.provider, Book.external_id],
                            set_=update_values,
                        )
                        session.execute(statement)
                    else:
                        record = session.scalar(
                            select(Book).where(
                                Book.provider == item.provider,
                                Book.external_id == item.external_id,
                            )
                        )
                        if record is None:
                            session.add(
                                Book(
                                    id=item.id,
                                    provider=item.provider,
                                    external_id=item.external_id,
                                    **values,
                                )
                            )
                        else:
                            for field, value in values.items():
                                setattr(record, field, value)
                    record = session.scalar(
                        select(Book).where(
                            Book.provider == item.provider,
                            Book.external_id == item.external_id,
                        )
                    )
                    if record is not None:
                        item.id = record.id
                session.commit()
                return result
        except SQLAlchemyError as exc:
            raise AppError(
                503, "SERVICE_UNAVAILABLE", "Não foi possível atualizar o catálogo."
            ) from exc

    @staticmethod
    def _to_item(record: Book) -> BookItem:
        return BookItem(
            id=record.id,
            title=record.title,
            authors=record.authors,
            description=record.description,
            genres=record.genres,
            subjects=record.subjects,
            publication_year=record.publication_year,
            cover_url=record.cover_url,
            external_url=record.external_url,
            provider=record.provider,
            external_id=record.external_id,
        )
