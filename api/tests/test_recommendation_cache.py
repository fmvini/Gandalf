from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.core.exceptions import AppError
from app.database.base import Base
from app.database.session import make_engine
from app.main import create_app
from app.models import RecommendationResult
from app.providers.local_catalog import BOOKS
from app.schemas.recommendation import DiscoveryRequest, ReadingRequest
from app.services.recommendation_cache import RecommendationCache
from app.services.recommendation_service import RecommendationService


@pytest.fixture
def database(tmp_path):
    url = f"sqlite:///{tmp_path / 'results.db'}"
    engine = make_engine(url)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    yield url, factory
    engine.dispose()


def test_snapshot_is_minimal_detached_and_published_after_reading_summary(database):
    _, factory = database
    service = RecommendationService(RecommendationCache(factory))
    result = service.reading(BOOKS[1], ReadingRequest(book_id=BOOKS[1].id, mode="CALM"))
    original = deepcopy(result["items"])
    result["items"].clear()
    loaded = service.get_result(result["recommendation_id"])
    assert set(loaded) == {"recommendation_id", "items", "playlist"}
    assert loaded["items"] == original
    assert loaded["playlist"] == result["playlist"]
    loaded["items"].clear()
    assert service.get_result(result["recommendation_id"])["items"] == original
    # Database-backed workers never retain a second, potentially stale cache.
    assert service.results == {}


def test_expiration_boundary_and_updates_or_reads_do_not_extend_ttl(
    database, monkeypatch
):
    _, factory = database
    clock = [1000.0]
    monkeypatch.setattr("app.services.recommendation_cache.time", lambda: clock[0])
    cache = RecommendationCache(factory)
    result = {"recommendation_id": str(uuid4()), "items": []}
    cache.put(result)
    clock[0] += 20
    assert cache.get(result["recommendation_id"]) == result
    cache.put(result)
    with factory() as session:
        row = session.get(RecommendationResult, UUID(result["recommendation_id"]))
        assert row.created_at == 1_000_000
        assert row.expires_at == 4_600_000
    clock[0] = 4600.0
    assert cache.get(result["recommendation_id"]) is None
    with factory() as session:
        assert (
            session.scalar(select(func.count()).select_from(RecommendationResult)) == 0
        )


def test_eviction_is_global_and_does_not_resurrect_from_another_worker(
    database, monkeypatch
):
    url, factory = database
    other_engine = make_engine(url)
    other = RecommendationService(RecommendationCache(sessionmaker(other_engine)))
    service = RecommendationService(RecommendationCache(factory))
    try:
        clock = [1000.0]
        monkeypatch.setattr("app.services.recommendation_cache.time", lambda: clock[0])
        first = service.discover("music", DiscoveryRequest(query="calma"))
        first_id = first["recommendation_id"]
        assert other.get_result(first_id)["items"] == first["items"]
        for _ in range(256):
            clock[0] += 1
            other.remember({"recommendation_id": str(uuid4()), "items": []})
        with factory() as session:
            assert (
                session.scalar(select(func.count()).select_from(RecommendationResult))
                == 256
            )
        for worker in [service, other]:
            with pytest.raises(AppError) as error:
                worker.get_result(first_id)
            assert error.value.status_code == 404
    finally:
        other_engine.dispose()


def _publish_in_process(url, count):
    engine = make_engine(url)
    cache = RecommendationCache(sessionmaker(engine))
    try:
        for _ in range(count):
            cache.put({"recommendation_id": str(uuid4()), "items": []})
    finally:
        engine.dispose()


def test_concurrent_sqlite_processes_enforce_global_capacity(database):
    url, factory = database
    with ProcessPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(_publish_in_process, url, 95) for _ in range(3)]
        for future in futures:
            future.result(timeout=60)
    with factory() as session:
        assert (
            session.scalar(select(func.count()).select_from(RecommendationResult))
            == 256
        )


def test_database_failure_returns_503_without_leaking_storage_details(database):
    _, factory = database
    cache = RecommendationCache(factory)
    with factory.begin() as session:
        session.execute(text("DROP TABLE recommendation_results"))
    for operation in [
        lambda: cache.put({"recommendation_id": str(uuid4()), "items": []}),
        lambda: cache.get(str(uuid4())),
        cache.prune,
    ]:
        with pytest.raises(AppError) as error:
            operation()
        assert error.value.status_code == 503
        assert error.value.code == "SERVICE_UNAVAILABLE"
        assert "recommendation_results" not in error.value.message


def test_two_api_instances_share_explanations_and_owner_scoped_saves(
    database, monkeypatch
):
    url, _ = database
    settings = Settings(
        _env_file=None,
        database_url=url,
        jwt_secret="cache-test-" + "s" * 64,
        book_provider="local",
        online_catalog=False,
    )
    with (
        TestClient(create_app(settings=settings)) as first,
        TestClient(create_app(settings=settings)) as second,
    ):
        result = first.post(
            "/api/v1/recommendations/read-with-music",
            json={
                "book_id": str(BOOKS[1].id),
                "mode": "CALM",
                "target_duration_min": 15,
            },
        ).json()
        source_id = result["recommendation_id"]
        explanation = (
            f"/api/v1/recommendations/{source_id}/items/"
            f"{result['items'][0]['item']['id']}/explanation"
        )
        assert second.get(explanation).json() == {
            "text": result["items"][0]["explanation"]
        }
        assert (
            second.get(
                explanation.replace(result["items"][0]["item"]["id"], str(uuid4()))
            ).status_code
            == 404
        )
        headers = []
        for name in ["ana", "bia"]:
            body = {
                "email": name + "@example.com",
                "username": name,
                "password": "uma-senha-longa-teste",
            }
            assert second.post("/api/v1/auth/register", json=body).status_code == 201
            token = second.post("/api/v1/auth/login", json=body).json()["access_token"]
            headers.append({"Authorization": "Bearer " + token})
        save = {"name": "Entre instâncias", "source_recommendation_id": source_id}
        assert second.post("/api/v1/playlists", json=save).status_code == 401
        created = second.post("/api/v1/playlists", json=save, headers=headers[0])
        assert created.status_code == 201
        playlist = created.json()
        assert [row["item"] for row in playlist["tracks"]] == [
            row["item"] for row in result["items"]
        ]
        path = "/api/v1/playlists/" + playlist["id"]
        assert first.get(path, headers=headers[0]).json() == playlist
        assert first.get(path, headers=headers[1]).status_code == 404
        assert first.delete(path, headers=headers[1]).status_code == 404
        # No stale memory snapshot can bypass expiration in the shared store.
        monkeypatch.setattr(
            "app.services.recommendation_cache.time", lambda: float(10**10)
        )
        expired = first.post("/api/v1/playlists", json=save, headers=headers[0])
        assert expired.status_code == 404
        assert second.get(explanation).status_code == 404
        assert second.get(path, headers=headers[0]).json() == playlist


def test_result_just_published_is_available_when_timestamps_tie(database, monkeypatch):
    _, factory = database
    cache = RecommendationCache(factory)
    monkeypatch.setattr("app.services.recommendation_cache.time", lambda: 1000.0)
    for index in range(257):
        # Descending UUIDs make the newest ID the oldest tie-break candidate.
        result = {"recommendation_id": str(UUID(int=1000 - index)), "items": []}
        cache.put(result)
        assert cache.get(result["recommendation_id"]) == result
    with factory() as session:
        assert (
            session.scalar(select(func.count()).select_from(RecommendationResult))
            == 256
        )
