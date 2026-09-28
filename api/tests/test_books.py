import asyncio
from uuid import UUID

import httpx
from fastapi.testclient import TestClient

from app.core.exceptions import UpstreamTimeout
from app.main import create_app
from app.providers.open_library import OpenLibraryProvider
from app.schemas.book import BookItem, BookSearchResponse


class FakeBookProvider:
    def __init__(self, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, int]] = []
        self.error = error

    async def search(self, title: str, limit: int) -> BookSearchResponse:
        self.calls.append((title, limit))
        if self.error:
            raise self.error
        return BookSearchResponse(
            items=[
                BookItem(
                    id=UUID("b66cf776-340a-48ca-8fbd-235d183dbde7"),
                    title="Duna",
                    authors=["Frank Herbert"],
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
            "ranking_version": None,
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
    assert requests[0].url.params["title"] == "O Senhor dos Anéis"
    assert requests[0].url.params["limit"] == "6"
    assert requests[0].headers["User-Agent"].startswith("Gandalf/")


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
