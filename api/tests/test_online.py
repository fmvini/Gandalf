import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from alembic import command
from app.core.config import Settings
from app.main import create_app
from app.models import AIUsage
from app.providers.musicbrainz import literal, normalize_recording
from app.services.online_store import OnlineStore


class Remote:
    def __init__(self):
        self.calls = []
        self.ai_status = 200
        self.catalog_status = 200
        self.bad_ai = False
        self.invalid_indices = False
        self.known_vocals = True
        self.kind = "books"

    def __call__(self, request):
        self.calls.append(request)
        if request.url.host == "api.groq.com":
            assert request.headers["Authorization"] == "Bearer test-secret-not-real"
            body = json.loads(request.content)
            assert body["response_format"]["json_schema"]["strict"] is True
            if self.ai_status != 200:
                return httpx.Response(
                    self.ai_status,
                    json={"error": "Do not expose provider response or credentials"},
                )
            schema = body["response_format"]["json_schema"]["name"]
            if schema == "Intent":
                data = {
                    "search_terms": ["fantasy" if self.kind == "books" else "ambient"],
                    "themes": ["fantasia" if self.kind == "books" else "calmo"],
                    "excluded_themes": [],
                    "references": [],
                    "vocals": "optional",
                    "energy": "any",
                }
            else:
                data = {
                    "choices": [
                        {
                            "index": 0,
                            "score": 0.95,
                            "vocals": "instrumental"
                            if self.known_vocals
                            else "unknown",
                            "energy": "low",
                        }
                    ]
                }
                if self.invalid_indices:
                    data["choices"] += [
                        {
                            "index": 999,
                            "score": 1.0,
                            "vocals": "unknown",
                            "energy": "unknown",
                        },
                        data["choices"][0],
                    ]
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": "not-json"
                                if self.bad_ai
                                else json.dumps(data)
                            }
                        }
                    ]
                },
            )
        if self.catalog_status != 200:
            return httpx.Response(self.catalog_status)
        if request.url.host == "openlibrary.org":
            return httpx.Response(
                200,
                json={
                    "numFound": 1,
                    "docs": [
                        {
                            "key": "/works/OL9999W",
                            "title": "External Fantasy",
                            "author_name": ["Example Author"],
                            "subject": ["Fantasy"],
                            "first_publish_year": 2000,
                        }
                    ],
                },
            )
        if request.url.host == "musicbrainz.org":
            assert "Gandalf/" in request.headers["User-Agent"]
            return httpx.Response(
                200,
                json={
                    "recordings": [
                        {
                            "id": "f5d899b8-20d5-407d-8727-e44f96f66e05",
                            "title": "External Ambient",
                            "artist-credit": [{"name": "Example Artist"}],
                            "length": 240000,
                            "tags": [{"name": "ambient"}],
                        }
                    ]
                },
            )
        raise AssertionError("Unexpected host: " + request.url.host)


@pytest.fixture
def online(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'online.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    command.upgrade(
        Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head"
    )
    settings = Settings(
        _env_file=None,
        database_url=url,
        online_catalog=True,
        groq_api_key="test-secret-not-real",
        ai_daily_limit=50,
    )
    remote = Remote()
    monkeypatch.setattr(
        "app.main.external_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(remote)),
    )
    return settings, remote


def test_online_books_use_real_candidates_and_cache_across_restart(online):
    settings, remote = online
    body = {"query": "Fantasia medieval", "limit": 5}
    for _ in range(2):
        with TestClient(create_app(settings=settings)) as client:
            result = client.post("/api/v1/recommendations/books", json=body)
            assert result.status_code == 200
            data = result.json()
            assert data["meta"]["ai_used"] is True
            assert data["meta"]["sources"] == ["open_library"]
            item = data["items"][0]["item"]
            assert item["title"] == "External Fantasy"
            assert client.get("/api/v1/books/" + item["id"]).status_code == 200
            why = client.get(
                f"/api/v1/recommendations/{data['recommendation_id']}/items/{item['id']}/explanation"
            )
            assert "Fantasy" in why.json()["text"]
            assert "ausência" in why.json()["text"]
            assert "test-secret" not in result.text
            status = client.get("/api/v1/system/status")
            assert status.json()["ai"]["configured"] is True
            assert "test-secret" not in status.text
    assert len([call for call in remote.calls if call.url.host == "api.groq.com"]) == 2
    assert (
        len([call for call in remote.calls if call.url.host == "openlibrary.org"]) == 1
    )


@pytest.mark.parametrize(
    "state", ["quota", "invalid", "unavailable", "no_key", "local_limit"]
)
def test_ai_failures_fall_back_without_invented_ai(online, state):
    settings, remote = online
    if state == "quota":
        remote.ai_status = 429
    if state == "unavailable":
        remote.ai_status = 503
    if state == "invalid":
        remote.bad_ai = True
    if state == "no_key":
        settings = settings.model_copy(
            update={
                "groq_api_key": Settings(_env_file=None, groq_api_key="").groq_api_key
            }
        )
    if state == "local_limit":
        settings = settings.model_copy(update={"ai_daily_limit": 0})
    with TestClient(create_app(settings=settings)) as client:
        data = client.post(
            "/api/v1/recommendations/books", json={"query": "fantasia"}
        ).json()
        assert data["meta"]["degraded"] is True
        assert data["meta"]["ai_used"] is False
        assert data["items"]
        assert "test-secret" not in json.dumps(data)
        if state in {"no_key", "local_limit"}:
            assert all(call.url.host != "api.groq.com" for call in remote.calls)


def test_music_catalog_duration_filters_and_invalid_indices(online):
    settings, remote = online
    remote.kind, remote.invalid_indices = "music", True
    with TestClient(create_app(settings=settings)) as client:
        data = client.post(
            "/api/v1/recommendations/music",
            json={
                "query": "Música calma instrumental",
                "filters": {"vocals": "none", "energy": "low"},
            },
        ).json()
        assert len(data["items"]) == 1
        item = data["items"][0]["item"]
        assert item["provider"] == "musicbrainz"
        assert item["duration_ms"] == 240000
        assert item["classification_source"] == "ai_estimate"
        stored = client.get("/api/v1/music/" + item["id"]).json()
        assert stored["has_vocals"] is None  # AI guesses never overwrite source data.
        assert "classification_source" not in stored
        assert client.get("/api/v1/music/" + str(uuid4())).status_code == 404
        first = client.get("/api/v1/music/search?q=ambient")
        second = client.get("/api/v1/music/search?q=ambient")
        assert first.json() == second.json()
        assert first.status_code == 200


def test_unknown_vocals_are_not_treated_as_instrumental(online):
    settings, remote = online
    remote.kind, remote.known_vocals = "music", False
    with TestClient(create_app(settings=settings)) as client:
        data = client.post(
            "/api/v1/recommendations/music",
            json={"query": "ambient instrumental", "filters": {"vocals": "none"}},
        ).json()
        assert data["items"] == []


def test_reading_external_book_uses_known_recording_duration(online):
    settings, remote = online
    remote.kind = "music"
    with TestClient(create_app(settings=settings)) as client:
        book = client.get("/api/v1/books/search?q=External").json()["items"][0]
        data = client.post(
            "/api/v1/recommendations/read-with-music",
            json={"book_id": book["id"], "mode": "FOCUS", "target_duration_min": 30},
        ).json()
        assert data["items"]
        assert data["playlist"] == {
            "tracks_count": 1,
            "total_duration_ms": 240000,
            "duration_estimated": False,
        }
        assert "não preenche" in data["meta"]["hint"]


def test_catalog_failure_preserves_local_picker_and_recommendations(online):
    settings, remote = online
    remote.catalog_status, remote.ai_status = 503, 503
    with TestClient(create_app(settings=settings)) as client:
        book = client.get("/api/v1/books/search?q=Duna").json()["items"][0]
        assert book["provider"] == "local"
        assert client.get("/api/v1/books/" + book["id"]).status_code == 200
        data = client.post(
            "/api/v1/recommendations/books", json={"query": "fantasia"}
        ).json()
        assert data["items"]
        assert data["meta"]["degraded"] is True


def test_daily_ai_allowance_is_atomic_and_persistent(online):
    settings, _ = online
    with TestClient(create_app(settings=settings)) as client:
        store = OnlineStore(client.app.state.session_factory)
        with ThreadPoolExecutor(max_workers=4) as pool:
            allowed = list(pool.map(lambda _: store.reserve_ai_call(3), range(12)))
        assert sum(allowed) == 3
    with TestClient(create_app(settings=settings)) as client:
        store = OnlineStore(client.app.state.session_factory)
        assert not store.reserve_ai_call(3)
        with client.app.state.session_factory() as session:
            assert session.scalar(select(AIUsage.calls)) == 3


def test_music_normalization_and_query_escaping():
    assert normalize_recording({"id": "invalid", "title": "bad"}) is None
    assert (
        normalize_recording(
            {"id": str(uuid4()), "title": "bad", "artist-credit": [{"name": None}]}
        )
        is None
    )
    normalized = normalize_recording(
        {
            "id": str(uuid4()),
            "title": "Valid",
            "artist-credit": [{"name": "Artist"}],
            "tags": None,
            "length": True,
        }
    )
    assert normalized["duration_ms"] is None
    assert normalized["tags"] == []
    assert literal('a" OR *:*') == '"a\\" OR \\*\\:\\*"'


def test_music_timeout_and_invalid_payload(online, monkeypatch):
    settings, _ = online
    for invalid in [True, False]:

        def broken(request):
            if invalid:
                return httpx.Response(200, json={"recordings": None})
            raise httpx.ReadTimeout("unavailable", request=request)

        monkeypatch.setattr(
            "app.main.external_client",
            lambda: httpx.AsyncClient(transport=httpx.MockTransport(broken)),
        )
        with TestClient(create_app(settings=settings)) as client:
            assert client.get("/api/v1/music/search?q=anything").status_code == 503
