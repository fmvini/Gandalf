from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.providers.local_catalog import BOOKS, MUSIC
from app.schemas.recommendation import DiscoveryRequest, MusicFilters
from app.services.recommendation_service import RecommendationService, interpret


@pytest.fixture
def client(monkeypatch):
    async def prohibit_network(*args, **kwargs):
        raise AssertionError("Local recommendations must not call external services")

    monkeypatch.setattr(httpx.AsyncClient, "send", prohibit_network)
    with TestClient(
        create_app(
            settings=Settings(_env_file=None, database_url=None, book_provider="local")
        )
    ) as client:
        yield client


def test_music_filters_ranking_and_explanations(client):
    response = client.post(
        "/api/v1/recommendations/music",
        json={
            "query": "Músicas calmas para estudar",
            "filters": {"vocals": "none", "energy": "low"},
            "limit": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert all(
        not row["item"]["has_vocals"] and row["item"]["energy"] == "low"
        for row in data["items"]
    )
    assert all("calmo" in row["item"]["tags"] for row in data["items"])
    first = data["items"][0]["item"]
    explanation = client.get(
        f"/api/v1/recommendations/{data['recommendation_id']}/items/{first['id']}/explanation"
    )
    assert explanation.status_code == 200
    assert "calmo" in explanation.json()["text"]
    assert "instrumental" in explanation.json()["text"]
    assert (
        client.get(
            f"/api/v1/recommendations/{data['recommendation_id']}/items/{uuid4()}/explanation"
        ).status_code
        == 404
    )
    assert first["links"]["search"].startswith("https://www.youtube.com/results?")


def test_books_negation_and_reference(client):
    data = client.post(
        "/api/v1/recommendations/books",
        json={"query": "Gostei de O Hobbit, quero fantasia sem romance"},
    ).json()
    assert data["items"]
    assert "romance" in data["parsed_query"]["excluded_themes"]
    assert all("romance" not in row["item"]["genres"] for row in data["items"])
    assert all(row["item"]["title"] != "O Hobbit" for row in data["items"])
    assert "O Hobbit" in data["parsed_query"]["references"]


def test_reference_music_and_explicit_filters_override_language(client):
    data = client.post(
        "/api/v1/recommendations/music",
        json={
            "query": "Parecidas com No Surprises, instrumental",
            "filters": {"vocals": "required"},
        },
    ).json()
    assert data["items"]
    assert all(
        row["item"]["has_vocals"] and row["item"]["title"] != "No Surprises"
        for row in data["items"]
    )


def test_unknown_query_returns_honest_empty_state(client):
    data = client.post(
        "/api/v1/recommendations/books", json={"query": "xyzabcdefgh"}
    ).json()
    assert data["items"] == []
    assert "catálogo local" in data["meta"]["hint"]
    assert (
        client.post(
            "/api/v1/recommendations/books",
            json={"query": "fantasia", "filters": {"vocals": "none"}},
        ).status_code
        == 422
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"query": "   "},
        {"query": "calma", "limit": 100},
        {"query": "calma", "filters": {"vocals": "invalid"}},
        {"query": "calma", "paid_provider": True},
    ],
)
def test_discovery_validation(client, payload):
    assert client.post("/api/v1/recommendations/music", json=payload).status_code == 422


def test_local_book_picker_and_reading(client):
    search = client.get("/api/v1/books/search?q=dune&limit=6")
    assert search.status_code == 200
    book = search.json()["items"][0]
    assert book["title"] == "Duna"
    assert client.get("/api/v1/books/" + book["id"]).json() == book
    assert (
        client.get("/api/v1/books/search?q=duna&provider=open_library").status_code
        == 422
    )
    response = client.post(
        "/api/v1/recommendations/read-with-music",
        json={
            "book_id": book["id"],
            "mode": "FOCUS",
            "vocals": "ANY",
            "target_duration_min": 120,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"]
    assert len({row["item"]["id"] for row in data["items"]}) == len(data["items"])
    assert all(
        not row["item"]["has_vocals"] and row["item"]["energy"] == "low"
        for row in data["items"]
    )
    assert data["playlist"]["duration_estimated"] is True
    assert data["playlist"]["total_duration_ms"] == len(data["items"]) * 300_000
    assert "não preenche" in data["meta"]["hint"]


def test_reading_validation_and_missing_book(client):
    assert (
        client.post(
            "/api/v1/recommendations/read-with-music", json={"book_id": str(uuid4())}
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/recommendations/read-with-music",
            json={"book_id": str(BOOKS[0].id), "mode": "CUSTOM", "context": " "},
        ).status_code
        == 422
    )
    for mode in ["IMMERSIVE", "CINEMATIC", "CALM", "CUSTOM"]:
        data = client.post(
            "/api/v1/recommendations/read-with-music",
            json={
                "book_id": str(BOOKS[1].id),
                "mode": mode,
                "context": "aventura",
                "vocals": "MINIMAL",
                "target_duration_min": 30,
            },
        ).json()
        assert data["items"]
        assert all(not row["item"]["has_vocals"] for row in data["items"])
        assert data["playlist"]["total_duration_ms"] <= 30 * 60_000


def test_memory_is_bounded_and_explanations_expire(monkeypatch):
    service = RecommendationService()
    body = DiscoveryRequest(query="calma")
    first = service.discover("music", body)
    for _ in range(260):
        service.discover("music", body)
    assert len(service.results) == 256
    assert first["recommendation_id"] not in service.results
    monkeypatch.setattr(
        "app.services.recommendation_service.monotonic", lambda: float("inf")
    )
    service._prune()
    assert not service.results


def test_catalog_integrity_and_negation():
    assert len({item["id"] for item in MUSIC}) == len(MUSIC)
    assert len({book.id for book in BOOKS}) == len(BOOKS)
    assert interpret("fantasia sem romance")[1] == {"romance"}
    assert interpret("sem tristeza mas calmo")[0] == {"calmo"}


@pytest.mark.parametrize(
    "query,vocals,allowed_energy",
    [
        ("não quero instrumental", True, {"low", "medium", "high"}),
        ("sem letras", False, {"low", "medium", "high"}),
        ("energia média", None, {"medium"}),
        ("sem energia alta", None, {"low", "medium"}),
        ("sem energia baixa", None, {"medium", "high"}),
        ("sem energia alta nem energia média", None, {"low"}),
        ("instrumental sem energia alta", False, {"low", "medium"}),
    ],
)
def test_inferred_constraints_filter_actual_results(
    client, query, vocals, allowed_energy
):
    response = client.post("/api/v1/recommendations/music", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert data["items"]
    for row in data["items"]:
        assert row["item"]["energy"] in allowed_energy
        if vocals is not None:
            assert row["item"]["has_vocals"] is vocals
        if data["parsed_query"]["excluded_energy"]:
            assert "Exclui energia" in row["explanation"]


def test_explicit_energy_exclusions_and_validation(client):
    response = client.post(
        "/api/v1/recommendations/music",
        json={"query": "energia alta", "filters": {"excluded_energy": ["high"]}},
    )
    assert response.status_code == 200
    assert response.json()["items"]
    assert all(row["item"]["energy"] != "high" for row in response.json()["items"])
    for filters in [
        {"energy": "high", "excluded_energy": ["high"]},
        {"excluded_energy": ["invalid"]},
    ]:
        assert (
            client.post(
                "/api/v1/recommendations/music",
                json={"query": "música", "filters": filters},
            ).status_code
            == 422
        )
    assert (
        client.post(
            "/api/v1/recommendations/books",
            json={"query": "fantasia", "filters": {"excluded_energy": ["high"]}},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/recommendations/music", json={"query": "instrumental com voz"}
        ).status_code
        == 422
    )


@pytest.mark.parametrize("title", ["Duna", "O Hobbit", "O Jardim Secreto"])
def test_calm_and_focus_have_distinct_order_with_same_hard_filters(client, title):
    book = next(book for book in BOOKS if book.title == title)
    orders = {}
    for mode in ("FOCUS", "CALM"):
        response = client.post(
            "/api/v1/recommendations/read-with-music",
            json={
                "book_id": str(book.id),
                "mode": mode,
                "vocals": "INSTRUMENTAL",
                "target_duration_min": 25,
            },
        )
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 5
        assert all(
            not row["item"]["has_vocals"] and row["item"]["energy"] == "low"
            for row in items
        )
        orders[mode] = [row["item"]["id"] for row in items]
        if mode == "CALM":
            assert all("reading_mode" in row["scores"] for row in items)
            assert any("Em empates" in row["explanation"] for row in items)
    assert orders["FOCUS"] != orders["CALM"]


def test_calm_preference_only_breaks_ties_and_preserves_context_priority():
    source = [
        {
            "id": "a",
            "title": "A Cinema",
            "artist": "A",
            "tags": ["calmo", "cinematográfico"],
        },
        {"id": "b", "title": "B Piano", "artist": "B", "tags": ["calmo"]},
        {
            "id": "c",
            "title": "Z Ambient",
            "artist": "C",
            "tags": ["calmo", "atmosférico"],
        },
    ]
    service = RecommendationService()

    def rank(themes, mode):
        return service._rank(
            source, themes, set(), MusicFilters(), 3, set(), [], reading_mode=mode
        )["items"]

    assert [r["item"]["id"] for r in rank({"calmo"}, "FOCUS")] == ["a", "b", "c"]
    assert [r["item"]["id"] for r in rank({"calmo"}, "CALM")] == ["c", "b", "a"]
    assert rank({"calmo", "cinematográfico"}, "CALM")[0]["item"]["id"] == "a"
