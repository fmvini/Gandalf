"""Re-roll contracts with local catalog and fake external/AI providers only."""

import asyncio
from collections import Counter
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.ai.groq import Choice, Intent, Selection
from app.core.config import Settings
from app.core.exceptions import AppError
from app.main import create_app
from app.providers.local_catalog import BOOKS, MUSIC
from app.schemas.book import BookItem, BookSearchResponse
from app.schemas.recommendation import BookDiscoveryRequest, MusicDiscoveryRequest
from app.services.online_recommendations import OnlineRecommendationService


class AI:
    def __init__(self, fail=False, reject=False):
        self.fail, self.reject = fail, reject
        self.calls = []

    async def interpret(self, query, kind):
        self.calls.append(("interpret", query, kind))
        if self.fail:
            raise AppError(429, "AI_QUOTA", "Cota indisponível.")
        return Intent(
            search_terms=["ambient" if kind == "music" else "fantasy"],
            themes=["calmo" if kind == "music" else "fantasia"],
            excluded_themes=[],
            references=[],
            vocals="optional",
            energy="any",
        )

    async def select(self, query, kind, candidates, filters, limit):
        self.calls.append(("select", query, filters, limit))
        counts, indices = Counter(), []
        for i, item in enumerate(candidates):
            creator = item.get("artist", str(item.get("authors")))
            if counts[creator] < 2:
                indices.append(i)
                counts[creator] += 1
            if len(indices) == limit:
                break
        return Selection(
            choices=[
                Choice(
                    index=i,
                    score=0.1 if self.reject else 0.9,
                    vocals="instrumental",
                    energy="low",
                )
                for i in indices
            ]
        )


class Catalog:
    def __init__(self, pages=2, fail=False, duplicates=False):
        self.pages, self.fail, self.duplicates = pages, fail, duplicates
        self.calls = []

    async def search(self, term, limit, *, by_tag=False, offset=0):
        self.calls.append((term, limit, by_tag, offset))
        if self.fail:
            raise AppError(503, "MUSIC_PROVIDER_UNAVAILABLE", "Fonte indisponível.")
        items = [
            {
                "id": str(UUID(int=1000 + offset + i)),
                "title": f"Track {offset + i}",
                "artist": f"Artist {i // 3}",
                "provider": "musicbrainz",
                "tags": ["ambient"],
                "has_vocals": False,
                "energy": "low",
            }
            for i in range(15)
            if offset < self.pages * 15
        ]
        if self.duplicates and items:
            items[1] = {**items[0], "title": "Changed label"}
            items[2] = {**items[0], "id": str(UUID(int=9999))}
        return {"items": items, "has_more": offset + 15 < self.pages * 15}

    async def discover(self, term, limit, *, offset=0):
        data = await self.search(term, limit, offset=offset)
        return BookSearchResponse(
            total=self.pages * 15,
            items=[
                BookItem(
                    id=UUID(item["id"]),
                    title=item["title"],
                    authors=[item["artist"]],
                    subjects=["Fantasy"],
                    external_id=f"OL{offset + i}W",
                    external_url="https://openlibrary.org",
                )
                for i, item in enumerate(data["items"])
            ],
        )


@pytest.mark.parametrize("kind", ["music", "books"])
def test_local_http_reroll_exhaustion_preserves_filters_and_sources(kind):
    with TestClient(create_app(settings=Settings(_env_file=None))) as client:
        seen = set()
        for _ in range(30):
            response = client.post(
                f"/api/v1/recommendations/{kind}",
                json={
                    "query": "calmo" if kind == "music" else "fantasia",
                    "filters": {"vocals": "none", "energy": "low"}
                    if kind == "music"
                    else {},
                    "limit": 2,
                    "offset": 300,
                    f"excluded_{'music' if kind == 'music' else 'book'}_ids": sorted(
                        seen
                    ),
                },
            )
            assert response.status_code == 200
            result = response.json()
            ids = {row["item"]["id"] for row in result["items"]}
            assert not ids & seen
            seen.update(ids)
            assert result["meta"]["next_offset"] is None
            assert all(
                row["item"].get("provider", "local") == "local"
                for row in result["items"]
            )
            if kind == "music":
                assert all(
                    row["item"]["has_vocals"] is False
                    and row["item"]["energy"] == "low"
                    for row in result["items"]
                )
            if not result["meta"]["has_more"]:
                break
        else:
            pytest.fail("Finite catalog must terminate")
        assert seen
        assert not client.post(
            f"/api/v1/recommendations/{kind}",
            json={
                "query": "calmo" if kind == "music" else "fantasia",
                f"excluded_{'music' if kind == 'music' else 'book'}_ids": sorted(seen),
                "filters": {"vocals": "none", "energy": "low"}
                if kind == "music"
                else {},
            },
        ).json()["items"]


@pytest.mark.parametrize(
    "body",
    [
        {"offset": -1},
        {"offset": 301},
        {"excluded_music_ids": ["bad"]},
        {"excluded_music_ids": [str(UUID(int=i)) for i in range(201)]},
        {"excluded_book_ids": []},
        {"limit": 26},
    ],
)
def test_music_http_validates_reroll_bounds(body):
    with TestClient(create_app(settings=Settings(_env_file=None))) as client:
        response = client.post(
            "/api/v1/recommendations/music", json={"query": "calmo", **body}
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("kind", ["music", "books"])
@pytest.mark.parametrize("fail_ai", [False, True])
def test_online_reroll_uses_exclusions_pages_filters_and_diversity(kind, fail_ai):
    ai, catalog = AI(fail=fail_ai), Catalog()
    service = OnlineRecommendationService(ai, catalog, catalog)
    schema = MusicDiscoveryRequest if kind == "music" else BookDiscoveryRequest
    seen = set()
    query = "Calmo sem energia alta" if kind == "music" else "Fantasia medieval"
    for offset in (0, 15):
        result = asyncio.run(
            service.recommend(
                kind,
                schema(
                    query=query,
                    limit=3,
                    offset=offset,
                    **(
                        {"filters": {"vocals": "none", "excluded_energy": ["high"]}}
                        if kind == "music"
                        else {}
                    ),
                    **{
                        f"excluded_{'music' if kind == 'music' else 'book'}_ids": sorted(
                            seen
                        )
                    },
                ),
            )
        )
        ids = {row["item"]["id"] for row in result["items"]}
        assert ids and not ids & seen
        assert len(ids) == len(result["items"]) <= 3
        seen.update(ids)
        assert (
            max(
                Counter(
                    row["item"].get("artist", str(row["item"].get("authors")))
                    for row in result["items"]
                ).values()
            )
            <= 2
        )
        assert result["meta"]["degraded"] is fail_ai
        assert result["meta"]["next_offset"] == (15 if offset == 0 else None)
        assert result["meta"]["has_more"] is True  # accepted extra candidate
        assert (
            service.get_result(result["recommendation_id"])["items"] == result["items"]
        )
    assert [call[3] for call in catalog.calls] == [0, 15]
    assert len(catalog.calls) == 2  # one page per request, no automatic scan
    assert all(call[1] == query for call in ai.calls)
    if not fail_ai and kind == "music":
        assert all(
            call[2]["vocals"] == "none" and call[2]["excluded_energy"] == ["high"]
            for call in ai.calls
            if call[0] == "select"
        )


@pytest.mark.parametrize("kind", ["music", "books"])
def test_rejected_candidates_and_offset_ceiling_do_not_promise_more(kind):
    catalog = Catalog(pages=100)
    service = OnlineRecommendationService(AI(reject=True), catalog, catalog)
    schema = MusicDiscoveryRequest if kind == "music" else BookDiscoveryRequest
    result = asyncio.run(
        service.recommend(kind, schema(query="fantasia calmo", offset=300))
    )
    assert result["items"] == []
    assert result["meta"]["has_more"] is False
    assert result["meta"]["next_offset"] is None


def test_provider_and_ai_failure_do_not_promise_more_without_candidates():
    service = OnlineRecommendationService(AI(fail=True), None, Catalog(fail=True))
    result = asyncio.run(
        service.recommend(
            "music",
            MusicDiscoveryRequest(
                query="calmo",
                excluded_music_ids=[item["id"] for item in MUSIC],
            ),
        )
    )
    assert result["items"] == []
    assert result["meta"]["degraded"] is True
    assert result["meta"]["has_more"] is False
    assert "indisponível" in result["meta"]["hint"]


def test_online_deduplicates_uuid_and_title_artist_before_ai_selection():
    service = OnlineRecommendationService(AI(), None, Catalog(duplicates=True))
    result = asyncio.run(
        service.recommend("music", MusicDiscoveryRequest(query="calmo", limit=25))
    )
    items = [row["item"] for row in result["items"]]
    assert len({item["id"] for item in items}) == len(items)
    assert len({(item["title"], item["artist"]) for item in items}) == len(items)


@pytest.mark.parametrize("kind", ["music", "books"])
def test_seen_limit_disables_continuation_without_dropping_exclusions(kind):
    service = OnlineRecommendationService(AI(), Catalog(pages=100), Catalog(pages=100))
    schema = MusicDiscoveryRequest if kind == "music" else BookDiscoveryRequest
    known = (
        [item["id"] for item in MUSIC]
        if kind == "music"
        else [str(book.id) for book in BOOKS]
    )
    exclusions = [*known, *[str(UUID(int=i + 1)) for i in range(200 - len(known))]]
    result = asyncio.run(
        service.recommend(
            kind,
            schema(
                query="fantasia calmo",
                **{
                    f"excluded_{'music' if kind == 'music' else 'book'}_ids": exclusions,
                },
            ),
        )
    )
    assert result["meta"]["has_more"] is False
    assert result["meta"]["next_offset"] is None
    assert not set(exclusions) & {row["item"]["id"] for row in result["items"]}


@pytest.mark.parametrize("kind", ["music", "books"])
def test_last_provider_page_containing_only_seen_ids_is_exhausted(kind):
    catalog = Catalog(pages=1)
    service = OnlineRecommendationService(AI(), catalog, catalog)
    schema = MusicDiscoveryRequest if kind == "music" else BookDiscoveryRequest
    known = (
        [item["id"] for item in MUSIC]
        if kind == "music"
        else [str(book.id) for book in BOOKS]
    )
    exclusions = [*known, *[str(UUID(int=1000 + i)) for i in range(15)]]
    result = asyncio.run(
        service.recommend(
            kind,
            schema(
                query="fantasia calmo",
                **{
                    f"excluded_{'music' if kind == 'music' else 'book'}_ids": exclusions
                },
            ),
        )
    )
    assert result["items"] == []
    assert result["meta"]["has_more"] is False
    assert result["meta"]["next_offset"] is None
    assert len(catalog.calls) == 1
