"""Music port contracts: synthetic catalogs and mocked HTTP/AI only."""

import asyncio
from copy import deepcopy
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai.groq import Choice, Intent, Selection
from app.core.config import Settings
from app.database.base import Base
from app.main import create_app
from app.providers.base import MusicItem, MusicProvider, MusicSearchResult
from app.providers.local_catalog import BOOKS, MUSIC, LocalBookProvider
from app.providers.musicbrainz import MusicBrainzProvider, normalize_recording
from app.services.online_store import OnlineStore


def recording(number=0, provider="fixture_catalog", **overrides) -> MusicItem:
    external_id = f"recording-{number}"
    return {
        "id": str(uuid5(NAMESPACE_URL, f"https://{provider}.example/{external_id}")),
        "title": f"Synthetic track {number}",
        "artist": f"Synthetic artist {number}",
        "tags": ["ambient", "instrumental"],
        "duration_ms": 300000,
        "has_vocals": False,
        "energy": "low",
        "provider": provider,
        "external_id": external_id,
        "links": {"provider": f"https://{provider}.example/{external_id}"},
        "classification_source": "provider_tags",
        **overrides,
    }


class FakeMusic:
    def __init__(self, name="fixture_catalog", items=None, store=None):
        self.name = name
        self.items = (
            items if items is not None else [recording(i, name) for i in range(30)]
        )
        self.store = store
        self.calls = []
        self.closed = False

    async def search(
        self,
        query: str,
        limit: int = 20,
        *,
        by_tag: bool = False,
        offset: int = 0,
        reading: bool = False,
        instrumental: bool = False,
    ) -> MusicSearchResult:
        self.calls.append((query, limit, by_tag, offset, reading, instrumental))
        items = deepcopy(self.items[offset : offset + limit])
        if self.store is not None:
            self.store.save_music(items)
        return {
            "items": items,
            "total": len(items),
            "provider": self.name,
            "has_more": offset + limit < len(self.items),
        }

    async def aclose(self):
        self.closed = True


class FakeAI:
    def __init__(self, client):
        self.client = client
        self.vocals = "instrumental"
        self.energy = "low"
        self.use_search_terms = True
        self.calls = []

    async def interpret(self, query, kind):
        assert kind == "music"
        return Intent(
            search_terms=["ambient"] if self.use_search_terms else [],
            themes=["calmo"],
            excluded_themes=[],
            references=[],
            vocals="optional",
            energy="any",
        )

    async def select(self, query, kind, candidates, filters, limit, **kwargs):
        self.calls.append((deepcopy(candidates), filters, limit, kwargs))
        return Selection(
            choices=[
                Choice(index=i, score=0.95, vocals=self.vocals, energy=self.energy)
                for i, item in enumerate(candidates)
                if item.get("provider", "local") != "local"
            ][:limit]
        )


@pytest.fixture
def mocked_clients(monkeypatch):
    clients, requests, ais = [], [], []

    def remote(request):
        requests.append(request)
        assert request.url.host == "musicbrainz.org", "No real provider or LLM request"
        return httpx.Response(
            200,
            json={
                "count": 1,
                "recordings": [
                    {
                        "id": str(UUID(int=321)),
                        "title": "Mock MusicBrainz recording",
                        "artist-credit": [{"name": "Mock artist"}],
                        "length": 180000,
                        "tags": [{"name": "instrumental"}],
                    }
                ],
            },
        )

    def client_factory():
        client = httpx.AsyncClient(transport=httpx.MockTransport(remote))
        clients.append(client)
        return client

    def ai_factory(client, store, settings):
        ai = FakeAI(client)
        ais.append(ai)
        return ai

    monkeypatch.setattr("app.main.external_client", client_factory)
    monkeypatch.setattr("app.main.GroqClient", ai_factory)
    return clients, requests, ais


def app_for(provider=None, *, online=True, database_url=None):
    return create_app(
        settings=Settings(
            _env_file=None,
            database_url=database_url,
            online_catalog=online,
            book_provider="local",
            groq_api_key="",
        ),
        book_provider=LocalBookProvider(),
        music_provider=provider,
    )


def test_factory_injection_routes_search_discovery_reroll_and_reading(mocked_clients):
    provider: MusicProvider = FakeMusic()
    application = app_for(provider)
    with TestClient(application) as client:
        search = client.get(
            "/api/v1/music/search", params={"q": "public title", "limit": 3}
        )
        assert search.status_code == 200
        assert search.json()["provider"] == provider.name
        assert provider.calls == [("public title", 3, False, 0, False, False)]
        body = {
            "query": "Música calma",
            "limit": 3,
            "filters": {"vocals": "none", "energy": "low"},
        }
        first = client.post("/api/v1/recommendations/music", json=body)
        assert first.status_code == 200
        data = first.json()
        assert data["meta"]["sources"] == [provider.name]
        assert data["meta"]["has_more"] is True
        assert data["meta"]["next_offset"] == 15
        assert "MusicBrainz" not in data["meta"]["hint"]
        assert provider.name in data["meta"]["hint"]
        seen = [row["item"]["id"] for row in data["items"]]
        reroll = client.post(
            "/api/v1/recommendations/music",
            json={**body, "offset": 15, "excluded_music_ids": seen},
        )
        assert reroll.status_code == 200
        assert not set(seen) & {row["item"]["id"] for row in reroll.json()["items"]}
        assert provider.calls[1:3] == [
            ("ambient", 15, True, 0, False, False),
            ("ambient", 15, True, 15, False, False),
        ]
        reading = client.post(
            "/api/v1/recommendations/read-with-music",
            json={"book_id": str(BOOKS[0].id), "target_duration_min": 15},
        )
        assert reading.status_code == 200
        soundtrack = reading.json()
        assert soundtrack["playlist"]["duration_estimated"] is False
        assert soundtrack["playlist"]["total_duration_ms"] == 900000
        assert soundtrack["meta"]["sources"] == [provider.name]
        assert provider.name in soundtrack["meta"]["hint"]
        assert "MusicBrainz" not in str(soundtrack)
        assert all(provider.name in row["explanation"] for row in soundtrack["items"])
        assert all(call[1:] == (50, True, 0, True, True) for call in provider.calls[3:])
        assert application.state.music_provider is provider
        assert application.state.recommendation_service.music is provider
    clients, requests, ais = mocked_clients
    assert requests == []
    assert clients[0].is_closed
    assert ais[0].client is clients[0]
    assert provider.closed is False


@pytest.mark.parametrize("by_tag", [False, True])
def test_discovery_forwards_text_or_tag_search_without_changing_filters(
    mocked_clients, by_tag
):
    provider = FakeMusic(items=[recording()])
    with TestClient(app_for(provider)) as client:
        mocked_clients[2][0].use_search_terms = by_tag
        response = client.post(
            "/api/v1/recommendations/music",
            json={
                "query": "calmo",
                "filters": {"vocals": "none", "energy": "low"},
                "limit": 1,
            },
        )
        assert response.status_code == 200
        assert response.json()["items"][0]["item"]["id"] == provider.items[0]["id"]
        assert provider.calls == [
            ("ambient" if by_tag else "calmo", 15, by_tag, 0, False, False)
        ]


@pytest.mark.parametrize(
    "known_vocals,known_energy,choice_vocals,choice_energy,expected_source",
    [
        (False, "low", "vocal", "high", "provider_tags"),
        (True, "high", "instrumental", "low", "provider_tags"),
        (None, None, "unknown", "unknown", None),
        (None, None, "instrumental", "low", "ai_estimate"),
        (False, None, "vocal", "medium", "ai_estimate"),
        (None, "low", "vocal", "high", "ai_estimate"),
    ],
)
def test_estimates_only_fill_unknown_and_preserve_known_provenance(
    mocked_clients,
    known_vocals,
    known_energy,
    choice_vocals,
    choice_energy,
    expected_source,
):
    item = recording(has_vocals=known_vocals, energy=known_energy, tags=["jazz"])
    if known_vocals is None and known_energy is None:
        item.pop("classification_source")
    provider = FakeMusic(items=[item])
    with TestClient(app_for(provider)) as client:
        ai = mocked_clients[2][0]
        ai.vocals, ai.energy = choice_vocals, choice_energy
        response = client.post(
            "/api/v1/recommendations/music", json={"query": "jazz", "limit": 1}
        )
        assert response.status_code == 200
        row = response.json()["items"][0]
        result = row["item"]
        assert result["has_vocals"] is (
            known_vocals
            if known_vocals is not None
            else {"instrumental": False, "vocal": True}.get(choice_vocals)
        )
        assert result["energy"] == (
            known_energy
            if known_energy is not None
            else None
            if choice_energy == "unknown"
            else choice_energy
        )
        assert result.get("classification_source") == expected_source
        assert ("preenchidos pela IA" in row["explanation"]) is (
            expected_source == "ai_estimate"
        )
        assert ("preenchidos pela IA" in response.json()["meta"]["hint"]) is (
            expected_source == "ai_estimate"
        )
        assert provider.items == [item], "AI estimates must not mutate catalog metadata"


@pytest.mark.parametrize("energy", [None, "low"])
def test_unknown_vocals_never_pass_instrumental_filter(mocked_clients, energy):
    provider = FakeMusic(
        items=[recording(has_vocals=None, energy=energy, tags=["jazz"])]
    )
    with TestClient(app_for(provider)) as client:
        mocked_clients[2][0].vocals = "unknown"
        response = client.post(
            "/api/v1/recommendations/music",
            json={"query": "jazz", "filters": {"vocals": "none"}, "limit": 3},
        )
        assert response.status_code == 200
        assert response.json()["items"] == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"provider": "musicbrainz"},
        {"provider": "local"},
        {"duration_ms": None, "estimated_duration_ms": 300000},
        {"duration_ms": True},
        {"duration_ms": 89999},
        {"duration_ms": 600001},
        {"has_vocals": None, "tags": ["jazz"]},
        {"has_vocals": True, "tags": ["jazz"]},
    ],
)
def test_injected_reading_keeps_source_duration_and_vocal_gates(
    mocked_clients, overrides
):
    provider = FakeMusic(items=[recording(i, **overrides) for i in range(3)])
    with TestClient(app_for(provider)) as client:
        response = client.post(
            "/api/v1/recommendations/read-with-music",
            json={"book_id": str(BOOKS[0].id), "target_duration_min": 15},
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "SOUNDTRACK_INCOMPLETE"
    assert mocked_clients[1] == []


def test_reading_rejects_result_envelope_with_another_provider(mocked_clients):
    class Mismatched(FakeMusic):
        async def search(self, *args, **kwargs):
            return {**await super().search(*args, **kwargs), "provider": "musicbrainz"}

    with TestClient(app_for(Mismatched())) as client:
        response = client.post(
            "/api/v1/recommendations/read-with-music",
            json={"book_id": str(BOOKS[0].id), "target_duration_min": 15},
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "SOUNDTRACK_INCOMPLETE"


def test_reading_local_adapter_is_not_an_external_duration_source(mocked_clients):
    with TestClient(app_for(FakeMusic(name="local"))) as client:
        response = client.post(
            "/api/v1/recommendations/read-with-music",
            json={"book_id": str(BOOKS[0].id), "target_duration_min": 15},
        )
        assert response.status_code == 503


def test_reading_instrumental_tag_does_not_override_known_vocals(mocked_clients):
    provider = FakeMusic(items=[recording(i, has_vocals=True) for i in range(3)])
    with TestClient(app_for(provider)) as client:
        response = client.post(
            "/api/v1/recommendations/read-with-music",
            json={"book_id": str(BOOKS[0].id), "target_duration_min": 15},
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "SOUNDTRACK_INCOMPLETE"
    assert all(item["has_vocals"] is True for item in provider.items)


def test_reading_calm_tag_does_not_override_known_energy(mocked_clients):
    provider = FakeMusic(items=[recording(i, energy="high") for i in range(3)])
    with TestClient(app_for(provider)) as client:
        # Selection agrees with the explicit constraint, not the ambient tag.
        mocked_clients[2][0].energy = "high"
        response = client.post(
            "/api/v1/recommendations/read-with-music",
            json={
                "book_id": str(BOOKS[0].id),
                "target_duration_min": 15,
                "context": "energia alta",
            },
        )
        assert response.status_code == 200
        assert all(row["item"]["energy"] == "high" for row in response.json()["items"])
        assert all(
            row["item"]["classification_source"] == "provider_tags"
            for row in response.json()["items"]
        )


def test_reading_unknown_attributes_can_use_tags_with_explicit_provenance(
    mocked_clients,
):
    items = [recording(i, has_vocals=None, energy=None) for i in range(3)]
    for item in items:
        item.pop("classification_source")
    provider = FakeMusic(items=items)
    with TestClient(app_for(provider)) as client:
        response = client.post(
            "/api/v1/recommendations/read-with-music",
            json={"book_id": str(BOOKS[0].id), "target_duration_min": 15},
        )
        assert response.status_code == 200
        for row in response.json()["items"]:
            assert row["item"]["has_vocals"] is False
            assert row["item"]["energy"] == "low"
            assert row["item"]["classification_source"] == "provider_tags"
        assert (
            "não é uma medição acústica" in response.json()["items"][0]["explanation"]
        )
    assert provider.items == items


def test_reading_without_vocal_constraint_preserves_unknowns_and_flags(mocked_clients):
    items = [
        recording(i, has_vocals=None, energy=None, tags=["jazz"]) for i in range(3)
    ]
    for item in items:
        item.pop("classification_source")
    provider = FakeMusic(items=items)
    with TestClient(app_for(provider)) as client:
        response = client.post(
            "/api/v1/recommendations/read-with-music",
            json={
                "book_id": str(BOOKS[0].id),
                "target_duration_min": 15,
                "mode": "IMMERSIVE",
                "vocals": "ANY",
                "context": "jazz",
            },
        )
        assert response.status_code == 200
        for row in response.json()["items"]:
            assert row["item"]["has_vocals"] is None
            assert row["item"]["energy"] is None
            assert "classification_source" not in row["item"]
            assert "identifica a faixa como instrumental" not in row["explanation"]
    assert provider.calls == [
        ("soundtrack", 50, True, 0, True, False),
        ("ambient", 50, True, 0, True, False),
    ]


def test_offline_ignores_injection_and_never_opens_external_client(mocked_clients):
    provider = FakeMusic()
    with TestClient(app_for(provider, online=False)) as client:
        response = client.get("/api/v1/music/search", params={"q": MUSIC[0]["title"]})
        assert response.status_code == 200
        assert response.json()["provider"] == "local"
        assert (
            client.post(
                "/api/v1/recommendations/music", json={"query": "calmo"}
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/v1/recommendations/read-with-music",
                json={"book_id": str(BOOKS[0].id), "target_duration_min": 15},
            ).status_code
            == 200
        )
    assert provider.calls == []
    assert mocked_clients == ([], [], [])
    assert provider.closed is False


def test_app_isolation_default_and_owned_client_lifecycle(mocked_clients):
    injected = FakeMusic(name="alternate_fixture")
    default_app, injected_app = app_for(), app_for(injected)
    with TestClient(default_app) as default, TestClient(injected_app) as alternate:
        default_provider = default_app.state.music_provider
        assert isinstance(default_provider, MusicBrainzProvider)
        assert default_provider.name == "musicbrainz"
        assert default_provider.client is mocked_clients[0][0]
        assert (
            default_app.state.recommendation_service.ai.client
            is default_provider.client
        )
        assert default_provider.store is default_app.state.online_store
        assert (
            default_provider.ttl
            == default_app.state.settings.external_cache_ttl_seconds
        )
        assert injected_app.state.music_provider is injected
        assert not any(client.is_closed for client in mocked_clients[0])
        result = default.get(
            "/api/v1/music/search", params={"q": "public title", "limit": 1}
        )
        assert result.status_code == 200
        assert result.json()["provider"] == "musicbrainz"
        assert result.json()["items"][0]["has_vocals"] is None
        assert result.json()["items"][0]["energy"] is None
        assert (
            alternate.get(
                "/api/v1/music/search", params={"q": "public title", "limit": 1}
            ).json()["provider"]
            == injected.name
        )
    assert all(client.is_closed for client in mocked_clients[0])
    assert injected.closed is False
    with TestClient(default_app):
        assert default_app.state.music_provider is not default_provider
        assert default_app.state.music_provider.client is mocked_clients[0][2]
    assert mocked_clients[0][2].is_closed
    assert len(mocked_clients[1]) == 1


def test_adapter_persists_catalog_for_existing_detail_route(tmp_path, mocked_clients):
    url = f"sqlite:///{tmp_path / 'injected-catalog.db'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    try:
        store = OnlineStore(sessionmaker(engine))
        provider = FakeMusic(items=[recording()], store=store)
        with TestClient(app_for(provider, database_url=url)) as client:
            item_id = provider.items[0]["id"]
            assert client.get(f"/api/v1/music/{item_id}").status_code == 404
            result = client.get(
                "/api/v1/music/search", params={"q": "public title", "limit": 1}
            )
            assert result.status_code == 200
            detail = client.get(f"/api/v1/music/{item_id}")
            assert detail.status_code == 200
            assert detail.json() == provider.items[0]
        assert store.music_by_id(UUID(item_id)) == provider.items[0]
    finally:
        engine.dispose()


def test_musicbrainz_typed_search_preserves_cache_key_ids_nulls_and_flags():
    class Store:
        def __init__(self):
            self.data, self.gets, self.puts, self.saved = {}, [], [], []

        def get(self, provider, key, limit):
            self.gets.append((provider, key, limit))
            return self.data.get((provider, key, limit))

        def put(self, provider, key, limit, data, ttl):
            self.puts.append((provider, key, limit, ttl))
            self.data[provider, key, limit] = deepcopy(data)

        def save_music(self, items):
            self.saved.extend(deepcopy(items))

    raw = {
        "id": str(UUID(int=456)),
        "title": "Test",
        "artist-credit": [{"name": "Artist"}],
        "length": 300000,
        "tags": [{"name": "instrumental"}],
    }
    calls, store = [], Store()

    def remote(request):
        calls.append(request)
        return httpx.Response(200, json={"recordings": [raw], "count": 101})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(remote)) as client:
            provider: MusicProvider = MusicBrainzProvider(
                client, store, ttl=123, interval=0
            )
            kwargs = {
                "by_tag": True,
                "offset": 50,
                "reading": True,
                "instrumental": True,
            }
            first = await provider.search("Ambient", 50, **kwargs)
            second = await provider.search("Ambient", 50, **kwargs)
            assert first == second
            assert first["provider"] == provider.name == "musicbrainz"
            assert first["has_more"] is True
            item = first["items"][0]
            assert item["id"] == normalize_recording(raw)["id"]
            assert item["has_vocals"] is False
            assert item["energy"] is None
            assert item["classification_source"] == "provider_tags"
            assert item["external_id"] == raw["id"]

    asyncio.run(run())
    assert len(calls) == 1
    params = calls[0].url.params
    assert params["offset"] == "50" and params["limit"] == "50"
    assert params["query"].startswith('tag:"Ambient"')
    assert "dur:[90000 TO 600000]" in params["query"]
    assert "AND tag:instrumental" in params["query"]
    assert (
        store.gets == [("musicbrainz", "offset:50:reading-v2:True:tag:ambient", 50)] * 2
    )
    assert store.puts == [
        ("musicbrainz", "offset:50:reading-v2:True:tag:ambient", 50, 123)
    ]
    assert len(store.saved) == 1
