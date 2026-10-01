from copy import deepcopy
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.core.security import create_access_token
from app.database.session import make_engine
from app.main import create_app
from app.models import MusicCatalog, Playlist, PlaylistTrack, User
from app.providers.local_catalog import BOOKS, MUSIC

ROOT = "/api/v1/playlists"
SECRET = "playlist-test-only-" + "s" * 64
PASSWORD = "uma-senha-de-teste-longa"


def account(client, email="ana@example.com", username="ana"):
    created = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": PASSWORD},
    )
    assert created.status_code == 201
    return created.json(), login(client, email)


def login(client, email="ana@example.com"):
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


@pytest.fixture
def playlists(tmp_path: Path, monkeypatch):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'playlists.db'}",
        jwt_secret=SECRET,
        online_catalog=False,
        book_provider="local",
    )
    monkeypatch.setenv("DATABASE_URL", settings.database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    with TestClient(create_app(settings=settings)) as client:
        user, headers = account(client)
        yield client, settings, config, user, headers


def manual(client, headers, **values):
    return client.post(
        ROOT,
        headers=headers,
        json={"name": "Minha trilha", "music_ids": [MUSIC[0]["id"]], **values},
    )


def reading(client):
    response = client.post(
        "/api/v1/recommendations/read-with-music",
        json={"book_id": str(BOOKS[1].id), "mode": "CALM", "target_duration_min": 15},
    )
    assert response.status_code == 200
    assert response.json()["items"]
    return response.json()


def assert_no_playlists(settings):
    engine = make_engine(settings.database_url)
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Playlist)) == 0
        assert session.scalar(select(func.count()).select_from(PlaylistTrack)) == 0
    engine.dispose()


def test_reading_snapshot_can_save_sixty_tracks_and_rejects_larger_sources(playlists):
    client, _, _, _, headers = playlists
    source = reading(client)
    rows = [
        {
            "position": i + 1,
            "item": {**MUSIC[0], "id": str(uuid4()), "duration_ms": 120000},
        }
        for i in range(60)
    ]
    source["items"] = rows
    source["playlist"] = {
        "tracks_count": 60,
        "total_duration_ms": 7200000,
        "duration_estimated": False,
    }
    client.app.state.recommendation_service.remember(source)
    response = client.post(
        ROOT,
        headers=headers,
        json={
            "name": "Duas horas",
            "source_recommendation_id": source["recommendation_id"],
        },
    )
    assert response.status_code == 201
    saved = response.json()
    assert saved["tracks_count"] == 60
    assert saved["total_duration_ms"] == 7200000
    assert [t["item"]["id"] for t in saved["tracks"]] == [r["item"]["id"] for r in rows]
    assert client.get(ROOT + "/" + saved["id"], headers=headers).json() == saved
    source["items"].append({"position": 61, "item": {**MUSIC[0], "id": str(uuid4())}})
    client.app.state.recommendation_service.remember(source)
    assert (
        client.post(
            ROOT,
            headers=headers,
            json={
                "name": "Grande demais",
                "source_recommendation_id": source["recommendation_id"],
            },
        ).status_code
        == 422
    )


def test_manual_create_detail_list_and_delete(playlists):
    client, settings, _, _, headers = playlists
    ids = [item["id"] for item in reversed(MUSIC[:3])]
    response = manual(
        client, headers, name="  Terra Média  ", description="  Noite  ", music_ids=ids
    )
    assert response.status_code == 201
    saved = response.json()
    assert response.headers["Location"] == ROOT + "/" + saved["id"]
    assert saved["name"] == "Terra Média"
    assert saved["description"] == "Noite"
    assert saved["source"] == "MANUAL"
    assert saved["source_recommendation_id"] is None
    assert saved["tracks_count"] == 3
    assert saved["total_duration_ms"] == 900_000
    assert saved["duration_estimated"] is True
    assert saved["created_at"].endswith("Z")
    assert [track["position"] for track in saved["tracks"]] == [1, 2, 3]
    assert [track["item"]["id"] for track in saved["tracks"]] == ids
    assert [track["item"] for track in saved["tracks"]] == list(reversed(MUSIC[:3]))
    assert "user_id" not in saved
    assert client.get(response.headers["Location"], headers=headers).json() == saved
    page = client.get(ROOT, headers=headers).json()
    assert page["total"] == 1
    assert page["limit"] == 20 and page["offset"] == 0
    assert page["items"] == [
        {key: value for key, value in saved.items() if key != "tracks"}
    ]
    assert (
        client.delete(response.headers["Location"], headers=headers).status_code == 204
    )
    missing = client.get(response.headers["Location"], headers=headers)
    assert missing.status_code == 404
    assert (
        client.delete(response.headers["Location"], headers=headers).status_code == 404
    )
    assert client.get(ROOT, headers=headers).json()["items"] == []
    assert_no_playlists(settings)
    engine = make_engine(settings.database_url)
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(MusicCatalog)) == 3
    engine.dispose()


def test_reading_save_subset_and_restart_preserve_snapshots(playlists):
    client, settings, _, _, headers = playlists
    result = reading(client)
    ids = [row["item"]["id"] for row in result["items"]]
    created = client.post(
        ROOT,
        headers=headers,
        json={
            "name": "Leitura",
            "source_recommendation_id": result["recommendation_id"],
        },
    )
    assert created.status_code == 201
    saved = created.json()
    assert saved["source"] == "READ_WITH_MUSIC"
    assert saved["source_recommendation_id"] == result["recommendation_id"]
    assert [track["item"]["id"] for track in saved["tracks"]] == ids
    assert saved["total_duration_ms"] == result["playlist"]["total_duration_ms"]
    subset = client.post(
        ROOT,
        headers=headers,
        json={
            "name": "Trecho",
            "source_recommendation_id": result["recommendation_id"],
            "music_ids": list(reversed(ids[:2])),
        },
    )
    assert subset.status_code == 201
    assert [track["item"]["id"] for track in subset.json()["tracks"]] == list(
        reversed(ids[:2])
    )
    with TestClient(create_app(settings=settings)) as restarted:
        new_headers = login(restarted)
        assert restarted.app.state.recommendation_service.results == {}
        assert (
            restarted.get(ROOT + "/" + saved["id"], headers=new_headers).json() == saved
        )
        assert restarted.get(ROOT, headers=new_headers).json()["total"] == 2
        expired = restarted.post(
            ROOT,
            headers=new_headers,
            json={
                "name": "Depois",
                "source_recommendation_id": result["recommendation_id"],
            },
        )
        assert expired.status_code == 404


def test_account_isolation_and_pagination(playlists):
    client, _, _, _, headers = playlists
    other_user, other_headers = account(client, "bia@example.com", "bia")
    saved = [
        manual(client, headers, name=name).json() for name in ["Uma", "Duas", "Três"]
    ]
    other = manual(client, other_headers, name="Privada").json()
    first = client.get(ROOT + "?limit=2", headers=headers).json()
    second = client.get(ROOT + "?limit=2&offset=2", headers=headers).json()
    expected = sorted(
        saved, key=lambda row: (row["created_at"], row["id"]), reverse=True
    )
    assert first["total"] == second["total"] == 3
    assert [row["id"] for row in first["items"] + second["items"]] == [
        row["id"] for row in expected
    ]
    assert client.get(ROOT + "?offset=3", headers=headers).json()["items"] == []
    assert client.get(ROOT, headers=other_headers).json()["total"] == 1
    missing_id = str(uuid4())
    for other_id in [other["id"], missing_id]:
        for method in [client.get, client.delete]:
            response = method(ROOT + "/" + other_id, headers=headers)
            assert response.status_code == 404
            assert response.json()["error"]["message"] == "Playlist não encontrada."
    assert (
        client.get(ROOT + "/" + other["id"], headers=other_headers).status_code == 200
    )
    spoofed = manual(client, headers, user_id=other_user["id"])
    assert spoofed.status_code == 422


@pytest.mark.parametrize(
    "authentication", ["missing", "invalid", "expired", "inactive"]
)
def test_all_routes_require_an_active_account(playlists, authentication):
    client, settings, _, user, headers = playlists
    saved_id = manual(client, headers).json()["id"]
    if authentication == "missing":
        headers = {}
    elif authentication == "invalid":
        headers = {"Authorization": "Bearer forged"}
    elif authentication == "expired":
        headers = {
            "Authorization": "Bearer "
            + create_access_token(UUID(user["id"]), SECRET, -1)
        }
    else:
        engine = make_engine(settings.database_url)
        with Session(engine) as session:
            session.get(User, UUID(user["id"])).is_active = False
            session.commit()
        engine.dispose()
    assert manual(client, headers).status_code == 401
    assert client.get(ROOT, headers=headers).status_code == 401
    assert client.get(ROOT + "/" + saved_id, headers=headers).status_code == 401
    assert client.delete(ROOT + "/" + saved_id, headers=headers).status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "   ", "music_ids": [MUSIC[0]["id"]]},
        {"name": "x" * 121, "music_ids": [MUSIC[0]["id"]]},
        {"name": "Lista", "description": "x" * 1001, "music_ids": [MUSIC[0]["id"]]},
        {"name": "Lista"},
        {"name": "Lista", "music_ids": []},
        {"name": "Lista", "music_ids": [MUSIC[0]["id"], MUSIC[0]["id"]]},
        {"name": "Lista", "music_ids": [str(uuid4()) for _ in range(26)]},
        {"name": "Lista", "music_ids": ["bad-id"]},
        {"name": "Lista", "source_recommendation_id": "bad-id"},
        {"name": "Lista", "music_ids": [MUSIC[0]["id"]], "source": "MANUAL"},
        {"name": "Lista", "music_ids": [MUSIC[0]["id"]], "tracks": [MUSIC[0]]},
    ],
)
def test_invalid_payloads_do_not_write(playlists, payload):
    client, settings, _, _, headers = playlists
    response = client.post(ROOT, headers=headers, json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert_no_playlists(settings)


@pytest.mark.parametrize("query", ["limit=0", "limit=51", "offset=-1", "offset=100001"])
def test_invalid_pagination(playlists, query):
    client, _, _, _, headers = playlists
    assert client.get(ROOT + "?" + query, headers=headers).status_code == 422
    assert client.get(ROOT + "/bad-id", headers=headers).status_code == 422


def test_unknown_music_is_atomic_and_playlist_size_limit_is_supported(playlists):
    client, settings, _, _, headers = playlists
    unknown = manual(client, headers, music_ids=[MUSIC[0]["id"], str(uuid4())])
    assert unknown.status_code == 404
    assert_no_playlists(settings)
    assert (
        manual(client, headers, music_ids=[item["id"] for item in MUSIC]).json()[
            "tracks_count"
        ]
        == 25
    )


@pytest.mark.parametrize(
    "source", ["unknown", "expired", "books", "music", "empty", "mismatch"]
)
def test_source_validation_does_not_fall_back_to_manual(playlists, source):
    client, settings, _, _, headers = playlists
    result = reading(client)
    source_id = result["recommendation_id"]
    extra = {}
    if source == "unknown":
        source_id = str(uuid4())
        extra = {"music_ids": [MUSIC[0]["id"]]}
    elif source == "expired":
        client.app.state.recommendation_service.results[source_id] = (0, result)
    elif source in {"books", "music"}:
        source_id = client.post(
            "/api/v1/recommendations/" + source, json={"query": "fantasia calma"}
        ).json()["recommendation_id"]
    elif source == "empty":
        cached = client.app.state.recommendation_service.results[source_id][1]
        cached["items"] = []
    elif source == "mismatch":
        extra = {
            "music_ids": [
                next(
                    item["id"]
                    for item in MUSIC
                    if item["id"] not in {row["item"]["id"] for row in result["items"]}
                )
            ]
        }
    response = client.post(
        ROOT,
        headers=headers,
        json={"name": "Inválida", "source_recommendation_id": source_id, **extra},
    )
    assert response.status_code == (404 if source in {"unknown", "expired"} else 422)
    assert_no_playlists(settings)


@pytest.mark.parametrize(
    "durations,expected,estimated",
    [
        ([100_000, 200_000], 300_000, False),
        ([100_000, None], 400_000, True),
        ([None, None], 600_000, True),
    ],
)
def test_catalog_tracks_and_duration_preserve_saved_metadata(
    playlists, durations, expected, estimated
):
    client, settings, _, _, headers = playlists
    items = [
        {
            "id": str(uuid4()),
            "title": "Faixa " + str(i),
            "artist": "Artista",
            "duration_ms": duration,
            "provider": "musicbrainz",
            "links": {"provider": "https://musicbrainz.org/recording/example"},
        }
        for i, duration in enumerate(durations)
    ]
    client.app.state.online_store.save_music(items)
    created = manual(client, headers, music_ids=[item["id"] for item in items])
    assert created.status_code == 201
    saved = created.json()
    assert saved["total_duration_ms"] == expected
    assert saved["duration_estimated"] is estimated
    assert [track["item"] for track in saved["tracks"]] == items
    changed = deepcopy(items)
    changed[0]["title"] = "Título atualizado"
    client.app.state.online_store.save_music(changed)
    assert client.get(ROOT + "/" + saved["id"], headers=headers).json() == saved
    engine = make_engine(settings.database_url)
    with Session(engine) as session:
        with pytest.raises(IntegrityError):
            session.execute(
                delete(MusicCatalog).where(MusicCatalog.id == items[0]["id"])
            )
        session.rollback()
    engine.dispose()


def test_database_failure_rolls_back_playlist_catalog_and_tracks(playlists):
    client, settings, _, _, headers = playlists
    engine = make_engine(settings.database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TRIGGER reject_tracks BEFORE INSERT ON playlist_tracks BEGIN SELECT RAISE(ABORT, 'test failure'); END"
            )
        )
    response = manual(client, headers)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert_no_playlists(settings)
    with engine.begin() as connection:
        assert connection.scalar(select(func.count()).select_from(MusicCatalog)) == 0
        connection.execute(text("DROP TRIGGER reject_tracks"))
    assert manual(client, headers).status_code == 201
    engine.dispose()


def test_duration_total_can_exceed_postgresql_integer(playlists):
    client, _, _, _, headers = playlists
    items = [
        {
            "id": str(uuid4()),
            "title": "Gravação longa",
            "artist": "Artista",
            "duration_ms": 86_399_999,
        }
        for _ in range(25)
    ]
    client.app.state.online_store.save_music(items)
    created = manual(client, headers, music_ids=[item["id"] for item in items])
    assert created.status_code == 201
    assert created.json()["total_duration_ms"] == 25 * 86_399_999 > 2**31 - 1
    assert created.json()["duration_estimated"] is False


def test_account_deletion_cascades_playlists_and_tracks(playlists):
    client, settings, _, user, headers = playlists
    assert manual(client, headers).status_code == 201
    engine = make_engine(settings.database_url)
    with engine.begin() as connection:
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1
        connection.execute(delete(User).where(User.id == UUID(user["id"])))
    engine.dispose()
    assert_no_playlists(settings)
    assert client.get(ROOT, headers=headers).status_code == 401


def test_migration_round_trip_preserves_existing_accounts_and_catalog(playlists):
    client, settings, config, _, headers = playlists
    assert manual(client, headers).status_code == 201
    command.downgrade(config, "0005_online_catalog")
    assert client.get("/health/ready").status_code == 503
    response = client.get(ROOT, headers=headers)
    assert response.status_code == 503
    command.upgrade(config, "head")
    assert client.get("/health/ready").status_code == 200
    assert client.get(ROOT, headers=headers).json()["total"] == 0
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    engine = make_engine(settings.database_url)
    with engine.connect() as connection:
        assert {"playlists", "playlist_tracks"} <= set(
            inspect(connection).get_table_names()
        )
        assert connection.scalar(select(func.count()).select_from(MusicCatalog)) == 1
    engine.dispose()


def test_no_database_keeps_public_discovery_available():
    settings = Settings(
        _env_file=None, database_url=None, jwt_secret=SECRET, online_catalog=False
    )
    with TestClient(create_app(settings=settings)) as client:
        assert client.get(ROOT).status_code == 503
        assert (
            client.post(
                "/api/v1/recommendations/music", json={"query": "piano calmo"}
            ).status_code
            == 200
        )
