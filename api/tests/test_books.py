import asyncio
from pathlib import Path
from uuid import UUID

import httpx
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.core.exceptions import UpstreamTimeout
from app.main import create_app
from app.models import Book, ExternalSearchCache
from app.providers.open_library import OpenLibraryProvider, normalize_book
from app.schemas.book import BookItem, BookSearchResponse


class FakeBookProvider:
    name = "open_library"

    def __init__(self, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, int]] = []
        self.error = error
        self.title = "Duna"

    async def search(self, title: str, limit: int) -> BookSearchResponse:
        self.calls.append((title, limit))
        if self.error:
            raise self.error
        return BookSearchResponse(
            items=[
                BookItem(
                    id=UUID("b66cf776-340a-48ca-8fbd-235d183dbde7"),
                    title=self.title,
                    authors=["Frank Herbert"],
                    description="Uma jornada em Arrakis.",
                    subjects=["Ficção científica", "Deserto"],
                    external_url="https://openlibrary.org/works/OL893415W",
                    external_id="OL893415W",
                )
            ],
            total=1,
        )


def test_health_version_and_readiness_are_honest() -> None:
    with TestClient(create_app(book_provider=FakeBookProvider())) as client:
        assert client.get("/health").json() == {"status": "ok"}
        version = client.get("/version").json()
        assert version == {
            "app": "Gandalf",
            "version": "0.1.0",
            "ranking_version": "local-rules-v7",
        }
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json()["components"]["database"] == "down"


def test_book_search_returns_contract_and_caches_repeated_queries() -> None:
    provider = FakeBookProvider()
    with TestClient(create_app(book_provider=provider)) as client:
        first = client.get("/api/v1/books/search", params={"q": "  Duna  ", "limit": 6})
        second = client.get("/api/v1/books/search", params={"q": "duna", "limit": 6})
    assert first.status_code == 200
    assert first.json()["items"][0]["title"] == "Duna"
    assert first.json()["total"] == 1
    assert second.status_code == 200
    assert provider.calls == [("Duna", 6)]
    UUID(first.json()["items"][0]["id"])


def test_search_persists_catalog_and_detail_reads_from_database(
    tmp_path, monkeypatch
) -> None:
    database_url = f"sqlite:///{tmp_path / 'books.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    provider = FakeBookProvider()
    settings = Settings(database_url=database_url)

    with TestClient(create_app(settings=settings, book_provider=provider)) as client:
        search = client.get("/api/v1/books/search", params={"q": "Duna"})
        book_id = search.json()["items"][0]["id"]
        provider.title = "Duna edição atualizada"
        updated_search = client.get("/api/v1/books/search", params={"q": "Duna edição"})
        detail = client.get(f"/api/v1/books/{book_id}")
        missing = client.get("/api/v1/books/00000000-0000-0000-0000-000000000000")

    assert search.status_code == 200
    assert updated_search.status_code == 200
    assert detail.status_code == 200
    assert detail.json()["title"] == "Duna edição atualizada"
    assert detail.json()["external_id"] == "OL893415W"
    assert detail.json()["description"] == "Uma jornada em Arrakis."
    assert detail.json()["subjects"] == ["Ficção científica", "Deserto"]
    assert missing.status_code == 404
    engine = create_engine(database_url)
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Book)) == 1
    engine.dispose()


def test_search_cache_survives_restart_and_expires(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite:///{tmp_path / 'cache.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    settings = Settings(database_url=database_url, book_search_cache_ttl_seconds=60)
    first_provider = FakeBookProvider()
    with TestClient(
        create_app(settings=settings, book_provider=first_provider)
    ) as client:
        first = client.get("/api/v1/books/search", params={"q": "Duna", "limit": 6})
        different_limit = client.get(
            "/api/v1/books/search", params={"q": "Duna", "limit": 7}
        )
    assert first.status_code == different_limit.status_code == 200
    assert first_provider.calls == [("Duna", 6), ("Duna", 7)]

    second_provider = FakeBookProvider(UpstreamTimeout())
    with TestClient(
        create_app(settings=settings, book_provider=second_provider)
    ) as client:
        cached = client.get("/api/v1/books/search", params={"q": " dUnA ", "limit": 6})
        assert cached.json() == first.json()
        assert second_provider.calls == []
        engine = create_engine(database_url)
        with Session(engine) as session:
            record = session.query(ExternalSearchCache).filter_by(result_limit=6).one()
            record.expires_at = 0
            session.commit()
        engine.dispose()
        expired = client.get("/api/v1/books/search", params={"q": "Duna", "limit": 6})
    assert expired.status_code == 504
    assert second_provider.calls == [("Duna", 6)]


def test_empty_search_response_is_cached_with_database(tmp_path, monkeypatch) -> None:
    class EmptyBookProvider(FakeBookProvider):
        async def search(self, title: str, limit: int) -> BookSearchResponse:
            self.calls.append((title, limit))
            return BookSearchResponse(items=[], total=0)

    database_url = f"sqlite:///{tmp_path / 'empty-cache.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    settings = Settings(database_url=database_url)
    with TestClient(
        create_app(settings=settings, book_provider=EmptyBookProvider())
    ) as client:
        response = client.get("/api/v1/books/search", params={"q": "Inexistente"})
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}

    provider = FakeBookProvider(UpstreamTimeout())
    with TestClient(create_app(settings=settings, book_provider=provider)) as client:
        cached = client.get("/api/v1/books/search", params={"q": "Inexistente"})
    assert cached.json() == response.json()
    assert provider.calls == []


def test_book_detail_requires_configured_catalog() -> None:
    with TestClient(create_app(book_provider=FakeBookProvider())) as client:
        response = client.get("/api/v1/books/b66cf776-340a-48ca-8fbd-235d183dbde7")
    assert response.status_code == 503


def test_validation_and_upstream_error_have_standard_shape() -> None:
    with TestClient(
        create_app(book_provider=FakeBookProvider(UpstreamTimeout()))
    ) as client:
        invalid = client.get("/api/v1/books/search", params={"q": "x", "limit": 51})
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
        assert invalid.json()["error"]["request_id"] == invalid.headers["X-Request-ID"]
        blank = client.get("/api/v1/books/search", params={"q": "  "})
        assert blank.status_code == 422
        assert blank.json()["error"]["code"] == "VALIDATION_ERROR"
        timeout = client.get("/api/v1/books/search", params={"q": "Duna"})
        assert timeout.status_code == 504
        assert timeout.json()["error"]["code"] == "UPSTREAM_TIMEOUT"
        assert "request_id" in timeout.json()["error"]


def test_cors_allows_only_configured_frontend() -> None:
    with TestClient(create_app(book_provider=FakeBookProvider())) as client:
        allowed = client.options(
            "/api/v1/books/search",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        denied = client.options(
            "/api/v1/books/search",
            headers={
                "Origin": "https://untrusted.example",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert allowed.status_code == 200
    assert allowed.headers["Access-Control-Allow-Origin"] == "http://127.0.0.1:5173"
    assert "Access-Control-Allow-Origin" not in denied.headers


def test_open_library_provider_normalizes_real_response_shape() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "numFound": 2,
                "docs": [
                    {
                        "key": "/works/OL27448W",
                        "title": "O Senhor dos Anéis",
                        "author_name": ["J. R. R. Tolkien"],
                        "first_publish_year": 1954,
                        "cover_i": 258027,
                        "description": "  Uma jornada pela Terra-média.  ",
                        "subject": ["Fantasia", " Aventura ", "fantasia", None],
                    },
                    {"key": "/books/OL123M", "title": "Entrada inválida"},
                ],
            },
        )

    async def run() -> BookSearchResponse:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            provider = OpenLibraryProvider(client, request_interval_seconds=0)
            return await provider.search("O Senhor dos Anéis", 6)

    result = asyncio.run(run())
    assert result.total == 2
    assert len(result.items) == 1
    book = result.items[0]
    assert book.external_id == "OL27448W"
    assert book.external_url == "https://openlibrary.org/works/OL27448W"
    assert book.cover_url == "https://covers.openlibrary.org/b/id/258027-M.jpg"
    assert book.publication_year == 1954
    assert book.description == "Uma jornada pela Terra-média."
    assert book.subjects == ["Fantasia", "Aventura"]
    assert requests[0].url.params["title"] == "O Senhor dos Anéis"
    assert requests[0].url.params["limit"] == "6"
    assert "subject" in requests[0].url.params["fields"]
    assert "description" in requests[0].url.params["fields"]
    assert requests[0].headers["User-Agent"].startswith("Gandalf/")


def test_open_library_metadata_accepts_work_description_and_limits_size() -> None:
    book = normalize_book(
        {
            "key": "/works/OL27448W",
            "title": "O Senhor dos Anéis",
            "description": {"type": "/type/text", "value": "x" * 2100},
            "subject": ["Tema muito longo " * 12] + [f"Tema {i}" for i in range(20)],
        }
    )
    assert book is not None
    assert len(book.description or "") == 2000
    assert len(book.subjects) == 12
    assert all(len(subject) <= 120 for subject in book.subjects)


def test_open_library_timeout_is_mapped_to_domain_error() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(timeout)) as client:
            provider = OpenLibraryProvider(client, request_interval_seconds=0)
            await provider.search("Duna", 6)

    try:
        asyncio.run(run())
    except UpstreamTimeout:
        pass
    else:
        raise AssertionError("Timeout deveria virar UpstreamTimeout")
