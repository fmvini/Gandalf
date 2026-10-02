from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.main import create_app
from app.models import Favorite, MusicCatalog, Playlist, RecommendationResult
from app.providers.local_catalog import BOOKS
from app.schemas.favorite import FavoriteCreate
from app.services.favorite_service import FavoriteService

ROOT = "/api/v1/users/me/favorites"


def account(client, email="ana@example.com", username="ana"):
    password = "uma-senha-de-teste-longa"
    created = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert created.status_code == 201
    logged = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert logged.status_code == 200
    return created.json(), {"Authorization": "Bearer " + logged.json()["access_token"]}


@pytest.fixture
def favorites(tmp_path, monkeypatch):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'favorites.db'}",
        jwt_secret="favorites-test-only-" + "s" * 64,
        online_catalog=False,
        book_provider="local",
    )
    monkeypatch.setenv("DATABASE_URL", settings.database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    with TestClient(create_app(settings=settings)) as client:
        user, headers = account(client)
        yield client, settings, user, headers


def source(client, kind="music"):
    result = client.post(
        f"/api/v1/recommendations/{kind}",
        json={"query": "calma" if kind == "music" else "fantasia", "limit": 5},
    )
    assert result.status_code == 200
    assert result.json()["items"]
    return result.json()


def save(client, headers, result, index=0):
    return client.post(
        ROOT,
        headers=headers,
        json={
            "recommendation_id": result["recommendation_id"],
            "item_id": result["items"][index]["item"]["id"],
        },
    )


def status(client, headers, ids, kind="MUSIC"):
    return client.post(
        ROOT + "/status", headers=headers, json={"type": kind, "item_ids": ids}
    )


@pytest.mark.parametrize("kind,expected_type", [("music", "MUSIC"), ("books", "BOOK")])
def test_create_snapshots_and_deduplicates_without_refreshing(
    favorites, kind, expected_type
):
    client, _, _, headers = favorites
    result = source(client, kind)
    original = deepcopy(result["items"][0]["item"])
    response = save(client, headers, result)
    assert response.status_code == 201
    saved = response.json()
    assert set(saved) == {"id", "type", "item_id", "item", "created_at"}
    assert saved["type"] == expected_type and saved["item"] == original
    assert saved["item_id"] == original["id"]
    assert saved["created_at"].endswith("Z")
    assert (
        not {"score", "explanation", "query", "parsed_query", "user_id"} & saved.keys()
    )
    result["recommendation_id"] = str(uuid4())
    result["items"][0]["item"]["title"] = "Metadados posteriores"
    client.app.state.recommendation_service.remember(result)
    repeated = save(client, headers, result)
    assert repeated.status_code == 200 and repeated.json() == saved
    assert client.get(ROOT, headers=headers).json()["items"] == [saved]
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Favorite)) == 1
        assert session.scalar(select(func.count()).select_from(Playlist)) == 0
        assert session.scalar(select(func.count()).select_from(MusicCatalog)) == 0
        row = session.get(Favorite, UUID(saved["id"]))
        assert row.item == original
        assert str(row.source_recommendation_id) != result["recommendation_id"]


def test_owner_isolation_batch_status_and_idempotent_delete(favorites):
    client, _, _, headers = favorites
    _, other = account(client, "bia@example.com", "bia")
    result = source(client)
    saved = save(client, headers, result).json()
    item_id = saved["item_id"]
    requested = [item_id, str(uuid4())]
    assert status(client, headers, requested).json() == {
        "favorites": {item_id: saved["id"]}
    }
    assert status(client, other, requested).json() == {"favorites": {}}
    assert status(client, headers, requested, "BOOK").json() == {"favorites": {}}
    assert client.get(ROOT, headers=other).json()["total"] == 0
    # Identical response for missing/other owner; never deletes their favorite.
    assert client.delete(ROOT + "/" + saved["id"], headers=other).status_code == 204
    assert client.get(ROOT, headers=headers).json()["items"] == [saved]
    own = save(client, other, result)
    assert own.status_code == 201 and own.json()["id"] != saved["id"]
    assert client.delete(ROOT + "/" + saved["id"], headers=headers).status_code == 204
    assert client.delete(ROOT + "/" + saved["id"], headers=headers).status_code == 204
    assert status(client, headers, requested).json() == {"favorites": {}}
    assert client.get(ROOT, headers=other).json()["items"] == [own.json()]


def test_filtered_pagination_and_stable_ties(favorites):
    client, _, _, headers = favorites
    music = source(client)
    books = source(client, "books")
    saved = [save(client, headers, music, index).json() for index in range(3)]
    saved.append(save(client, headers, books).json())
    with client.app.state.session_factory.begin() as session:
        session.execute(
            update(Favorite).values(created_at=datetime(2026, 1, 1, tzinfo=UTC))
        )
    expected = sorted(saved, key=lambda row: row["id"], reverse=True)
    pages = [
        client.get(ROOT, headers=headers, params={"limit": 2, "offset": offset}).json()
        for offset in (0, 2)
    ]
    assert [row["id"] for page in pages for row in page["items"]] == [
        row["id"] for row in expected
    ]
    assert all(page["total"] == 4 and page["limit"] == 2 for page in pages)
    filtered = client.get(
        ROOT, headers=headers, params={"type": "MUSIC", "limit": 2, "offset": 1}
    ).json()
    assert filtered["total"] == 3 and len(filtered["items"]) == 2
    assert all(row["type"] == "MUSIC" for row in filtered["items"])
    assert (
        client.get(ROOT, headers=headers, params={"offset": 100_000}).json()["items"]
        == []
    )


def test_favorites_survive_restart_expiration_and_cache_eviction(favorites):
    client, settings, _, headers = favorites
    result = source(client)
    saved = save(client, headers, result).json()
    with TestClient(create_app(settings=settings)) as other_instance:
        assert other_instance.get(ROOT, headers=headers).json()["items"] == [saved]
        assert save(other_instance, headers, result).status_code == 200
    with client.app.state.session_factory.begin() as session:
        session.execute(update(RecommendationResult).values(expires_at=0))
    assert save(client, headers, result).status_code == 404
    assert client.get(ROOT, headers=headers).json()["items"] == [saved]
    assert status(client, headers, [saved["item_id"]]).json() == {
        "favorites": {saved["item_id"]: saved["id"]}
    }
    # Explicit cache clearing also leaves the independent saved snapshot intact.
    with client.app.state.session_factory.begin() as session:
        session.execute(text("DELETE FROM recommendation_results"))
    assert client.get(ROOT, headers=headers).json()["items"] == [saved]


def test_source_membership_unknown_origins_and_manual_payload_rejected(favorites):
    client, _, _, headers = favorites
    result = source(client)
    for body in (
        {
            "recommendation_id": str(uuid4()),
            "item_id": result["items"][0]["item"]["id"],
        },
        {"recommendation_id": result["recommendation_id"], "item_id": str(uuid4())},
    ):
        response = client.post(ROOT, headers=headers, json=body)
        assert (
            response.status_code == 404
            and response.json()["error"]["code"] == "NOT_FOUND"
        )
    body = {
        "recommendation_id": result["recommendation_id"],
        "item_id": result["items"][0]["item"]["id"],
    }
    for extra in (
        {"item": {"title": "Inventado"}},
        {"type": "BOOK"},
        {"user_id": str(uuid4())},
    ):
        assert (
            client.post(ROOT, headers=headers, json={**body, **extra}).status_code
            == 422
        )
    assert client.get(ROOT, headers=headers).json()["total"] == 0


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("GET", "", None),
        ("POST", "", {"recommendation_id": str(uuid4()), "item_id": str(uuid4())}),
        ("POST", "/status", {"type": "MUSIC", "item_ids": [str(uuid4())]}),
        ("DELETE", "/" + str(uuid4()), None),
    ],
)
def test_all_routes_require_authentication(favorites, method, path, body):
    client, _, _, _ = favorites
    for headers in ({}, {"Authorization": "Bearer invalid"}):
        response = client.request(method, ROOT + path, headers=headers, json=body)
        assert response.status_code == 401


@pytest.mark.parametrize(
    "params",
    [
        {"type": "MOVIE"},
        {"limit": 0},
        {"limit": 51},
        {"offset": -1},
        {"offset": 100001},
    ],
)
def test_collection_validation(favorites, params):
    client, _, _, headers = favorites
    response = client.get(ROOT, headers=headers, params=params)
    assert (
        response.status_code == 422
        and response.json()["error"]["code"] == "VALIDATION_ERROR"
    )


@pytest.mark.parametrize(
    "body",
    [
        {"type": "MUSIC", "item_ids": []},
        {"type": "MUSIC", "item_ids": [str(uuid4()) for _ in range(61)]},
        {"type": "BOOK", "item_ids": ["invalid"]},
        {"type": "MOVIE", "item_ids": [str(uuid4())]},
        {"type": "MUSIC", "item_ids": ["00000000-0000-0000-0000-000000000001"] * 2},
        {"type": "MUSIC", "item_ids": [str(uuid4())], "user_id": str(uuid4())},
    ],
)
def test_status_validation(favorites, body):
    client, _, _, headers = favorites
    assert client.post(ROOT + "/status", headers=headers, json=body).status_code == 422


def test_missing_tables_return_generic_503_without_partial_write(favorites):
    client, _, _, headers = favorites
    result = source(client)
    with client.app.state.engine.begin() as connection:
        connection.execute(text("DROP TABLE favorites"))
    responses = [
        save(client, headers, result),
        client.get(ROOT, headers=headers),
        status(client, headers, [result["items"][0]["item"]["id"]]),
        client.delete(ROOT + "/" + str(uuid4()), headers=headers),
    ]
    for response in responses:
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert "SELECT" not in response.text and "no such table" not in response.text


def test_missing_source_cache_does_not_write_or_break_private_reads(favorites):
    client, _, _, headers = favorites
    result = source(client)
    saved = save(client, headers, result).json()
    with client.app.state.engine.begin() as connection:
        connection.execute(text("DROP TABLE recommendation_results"))
    assert save(client, headers, result, 1).status_code == 503
    assert client.get(ROOT, headers=headers).json()["items"] == [saved]
    assert status(client, headers, [saved["item_id"]]).status_code == 200
    assert client.delete(ROOT + "/" + saved["id"], headers=headers).status_code == 204


def concurrent_save(url, user_id, body, result):
    from app.database.session import make_engine

    engine = make_engine(url)
    try:
        with Session(engine) as session:
            response, created = FavoriteService(session).create(
                UUID(user_id), FavoriteCreate(**body), result
            )
            return str(response.id), created
    finally:
        engine.dispose()


def test_concurrent_processes_deduplicate_atomically(favorites):
    client, settings, user, headers = favorites
    result = source(client)
    body = {
        "recommendation_id": result["recommendation_id"],
        "item_id": result["items"][0]["item"]["id"],
    }
    with ProcessPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(
                concurrent_save, settings.database_url, user["id"], body, result
            )
            for _ in range(6)
        ]
        responses = [future.result(timeout=30) for future in futures]
    assert len({favorite_id for favorite_id, _ in responses}) == 1
    assert sum(created for _, created in responses) == 1
    page = client.get(ROOT, headers=headers).json()
    assert page["total"] == 1 and page["items"][0]["item"] == result["items"][0]["item"]


def test_same_identity_of_different_types_is_separate(favorites):
    client, _, _, headers = favorites
    music, books = source(client), source(client, "books")
    books["items"][0]["item"]["id"] = music["items"][0]["item"]["id"]
    client.app.state.recommendation_service.remember(books)
    assert save(client, headers, music).status_code == 201
    assert save(client, headers, books).status_code == 201
    page = client.get(ROOT, headers=headers).json()
    assert page["total"] == 2 and {row["type"] for row in page["items"]} == {
        "MUSIC",
        "BOOK",
    }


def test_reading_item_preserves_duration_without_saving_playlist(favorites):
    client, _, _, headers = favorites
    response = client.post(
        "/api/v1/recommendations/read-with-music",
        json={"book_id": str(BOOKS[1].id), "mode": "CALM", "target_duration_min": 15},
    )
    assert response.status_code == 200
    result = response.json()
    saved = save(client, headers, result)
    assert saved.status_code == 201 and saved.json()["type"] == "MUSIC"
    assert saved.json()["item"] == result["items"][0]["item"]
    assert saved.json()["item"]["estimated_duration_ms"] == 300_000
    assert "playlist" not in saved.json()
    assert client.get("/api/v1/playlists", headers=headers).json()["total"] == 0


def test_commit_failure_rolls_back_favorite(favorites, monkeypatch):
    client, _, _, headers = favorites
    result = source(client)

    def fail_commit(session):
        raise OperationalError(
            "private SQL detail", {}, RuntimeError("database failed")
        )

    monkeypatch.setattr(Session, "commit", fail_commit)
    response = save(client, headers, result)
    assert response.status_code == 503 and "private SQL detail" not in response.text
    assert client.get(ROOT, headers=headers).json()["total"] == 0


def test_invalid_create_and_delete_ids(favorites):
    client, _, _, headers = favorites
    for body in (
        {},
        {"recommendation_id": "invalid", "item_id": str(uuid4())},
        {"recommendation_id": str(uuid4()), "item_id": "invalid"},
    ):
        assert client.post(ROOT, headers=headers, json=body).status_code == 422
    assert client.delete(ROOT + "/invalid", headers=headers).status_code == 422


@pytest.mark.parametrize("failure", ["missing_users", "connection"])
def test_authentication_database_failure_is_503_on_all_private_routes(
    favorites, monkeypatch, failure
):
    client, _, _, headers = favorites
    result = source(client)
    if failure == "missing_users":
        with client.app.state.engine.begin() as connection:
            connection.execute(text("DELETE FROM refresh_tokens"))
            connection.execute(text("DROP TABLE users"))
    else:

        def fail_get(session, *args, **kwargs):
            raise OperationalError(
                "private connection detail", {}, RuntimeError("down")
            )

        monkeypatch.setattr(Session, "get", fail_get)
    for response in (
        save(client, headers, result),
        client.get(ROOT, headers=headers),
        status(client, headers, [result["items"][0]["item"]["id"]]),
        client.delete(ROOT + "/" + str(uuid4()), headers=headers),
        client.get("/api/v1/auth/me", headers=headers),
    ):
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert "private connection detail" not in response.text
        assert "no such table" not in response.text
    assert client.get(ROOT).status_code == 401
    assert (
        client.get(ROOT, headers={"Authorization": "Bearer invalid"}).status_code == 401
    )


def concurrent_create_delete(url, user_id, body, result, deleting):
    from app.database.session import make_engine

    engine = make_engine(url)
    try:
        with Session(engine) as session:
            service = FavoriteService(session)
            for _ in range(15):
                if deleting:
                    favorite_id = session.scalar(
                        select(Favorite.id).where(
                            Favorite.user_id == UUID(user_id),
                            Favorite.type == "MUSIC",
                            Favorite.item_id == UUID(body["item_id"]),
                        )
                    )
                    service.delete(UUID(user_id), favorite_id or uuid4())
                else:
                    saved, _ = service.create(
                        UUID(user_id), FavoriteCreate(**body), result
                    )
                    assert saved.item == result["items"][0]["item"]
            return True
    finally:
        engine.dispose()


def test_concurrent_repeated_create_and_delete_return_detached_snapshots(favorites):
    client, settings, user, headers = favorites
    result = source(client)
    assert save(client, headers, result).status_code == 201
    body = {
        "recommendation_id": result["recommendation_id"],
        "item_id": result["items"][0]["item"]["id"],
    }
    with ProcessPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(
                concurrent_create_delete,
                settings.database_url,
                user["id"],
                body,
                result,
                deleting,
            )
            for deleting in (False, False, True)
        ]
        assert all(future.result(timeout=30) for future in futures)
    assert client.get(ROOT, headers=headers).json()["total"] <= 1
    final = save(client, headers, result)
    assert (
        final.status_code in (200, 201)
        and final.json()["item"] == result["items"][0]["item"]
    )
