import asyncio
from collections import Counter
from uuid import UUID

import httpx
import pytest

from app.ai.groq import Choice, GroqClient, Intent, Selection
from app.core.config import Settings
from app.core.exceptions import AppError
from app.providers.local_catalog import BOOKS
from app.schemas.book import BookItem, BookSearchResponse
from app.schemas.recommendation import BookDiscoveryRequest, ReadingRequest
from app.services.online_recommendations import OnlineRecommendationService
from app.services.reading_duration import reading_summary
from app.services.recommendation_service import RecommendationService


class AI:
    def __init__(self, kind="music", choose=5, fail=False):
        self.kind, self.choose, self.fail = kind, choose, fail
        self.selections = []
        self.interpretations = 0

    async def interpret(self, query, kind):
        self.interpretations += 1
        if self.fail:
            raise AppError(503, "AI_UNAVAILABLE", "IA indisponível.")
        return Intent(
            search_terms=["ambient" if kind == "music" else "fantasy"],
            themes=["calmo" if kind == "music" else "fantasia"],
            excluded_themes=[],
            references=[],
            vocals="optional",
            energy="any",
        )

    async def select(self, query, kind, candidates, filters, limit, **kwargs):
        self.selections.append((query, candidates, kwargs))
        external = [
            i
            for i, item in enumerate(candidates)
            if item.get("provider", "local") != "local"
        ]
        return Selection(
            choices=[
                Choice(index=i, score=0.95, vocals="instrumental", energy="low")
                for i in external[: self.choose]
            ]
        )


class Music:
    def __init__(self, duration=300000, pages=6, duplicate=False):
        self.duration, self.pages, self.duplicate = duration, pages, duplicate
        self.offsets = []

    async def search(self, term, limit, *, by_tag=False, offset=0):
        self.offsets.append(offset)
        page = offset // 15
        items = []
        if page < self.pages:
            for i in range(15):
                number = offset + i
                items.append(
                    {
                        "id": str(UUID(int=number + 1000)),
                        "title": f"Calm track {number}",
                        "artist": f"Artist {number}",
                        "provider": "musicbrainz",
                        "duration_ms": self.duration,
                        "tags": ["ambient"],
                        "has_vocals": None,
                        "energy": None,
                    }
                )
            if self.duplicate and page:
                items[0].update(title="Calm track 0", artist="Artist 0")
        return {"items": items, "has_more": page + 1 < self.pages}


class Books:
    def __init__(self):
        self.offsets = []

    async def discover(self, term, limit, *, offset=0):
        self.offsets.append(offset)
        return BookSearchResponse(
            total=45,
            items=[
                BookItem(
                    id=UUID(int=offset + i + 1000),
                    title=f"Fantasy {offset + i}",
                    authors=[f"Author {offset + i}"],
                    subjects=["Fantasy"],
                    external_id=f"OL{offset + i}W",
                    external_url="https://openlibrary.org",
                )
                for i in range(15)
            ],
        )


@pytest.mark.parametrize(
    "duration,estimated,count",
    [(300000, False, 18), (None, True, 18), (180000, False, 30)],
)
def test_reading_continues_after_five_choices_until_ninety_minutes(
    duration, estimated, count
):
    ai, music = AI(), Music(duration=duration)
    service = OnlineRecommendationService(ai, None, music)
    book = BOOKS[0].model_copy(
        update={"title": "Very long title " * 100, "subjects": ["Fantasy " * 200]}
    )
    context = "Piano instrumental suave " + "x" * 450
    result = asyncio.run(
        service.soundtrack(
            book,
            ReadingRequest(
                book_id=book.id, mode="CUSTOM", context=context, target_duration_min=90
            ),
        )
    )
    assert len(result["items"]) == count
    summary = result["playlist"]
    assert summary["target_met"] is True
    assert summary["shortfall_ms"] == 0
    assert summary["target_duration_ms"] == summary["total_duration_ms"] == 5400000
    assert summary["duration_estimated"] is estimated
    assert music.offsets == list(range(0, len(music.offsets) * 15, 15))
    assert all(context in query for query, _, _ in ai.selections)
    assert [kw["target_duration_ms"] for _, _, kw in ai.selections] == [
        5400000 - i * 5 * (duration or 300000) for i in range(len(ai.selections))
    ]
    assert len({row["item"]["id"] for row in result["items"]}) == count
    assert ai.interpretations == 1
    last = result["items"][-1]
    assert service.explanation(result["recommendation_id"], last["item"]["id"])["text"]


def test_reading_exhaustion_reports_actual_shortfall_and_rejects_duplicate_recordings():
    ai, music = AI(), Music(pages=2, duplicate=True)
    service = OnlineRecommendationService(ai, None, music)
    result = asyncio.run(
        service.soundtrack(
            BOOKS[0], ReadingRequest(book_id=BOOKS[0].id, target_duration_min=90)
        )
    )
    keys = [(r["item"]["title"], r["item"]["artist"]) for r in result["items"]]
    assert len(keys) == len(set(keys)) == 10
    assert result["playlist"]["target_met"] is False
    assert result["playlist"]["shortfall_ms"] == 40 * 60000
    assert "não preenche" in result["meta"]["hint"]
    assert len(music.offsets) <= 3


def test_reading_limits_rounds_and_creator_repeats_when_duration_is_short():
    music = Music(duration=1000, pages=100)
    service = OnlineRecommendationService(AI(choose=25), None, music)
    result = asyncio.run(
        service.soundtrack(
            BOOKS[0], ReadingRequest(book_id=BOOKS[0].id, target_duration_min=120)
        )
    )
    assert len(result["items"]) == 60
    assert len(music.offsets) == 4
    assert max(Counter(row["item"]["artist"] for row in result["items"]).values()) <= 2
    assert result["playlist"]["target_met"] is False


def test_reading_stops_after_six_rounds_when_ai_selects_too_few_tracks():
    music = Music(pages=100)
    service = OnlineRecommendationService(AI(choose=1), None, music)
    result = asyncio.run(
        service.soundtrack(
            BOOKS[0], ReadingRequest(book_id=BOOKS[0].id, target_duration_min=90)
        )
    )
    assert len(music.offsets) == 6
    assert result["playlist"]["tracks_count"] == 6
    assert result["playlist"]["shortfall_ms"] == 3600000


def test_reading_creator_limit_applies_across_all_pages():
    class SameArtist(Music):
        async def search(self, *args, **kwargs):
            data = await super().search(*args, **kwargs)
            for item in data["items"]:
                item["artist"] = "Repeated artist"
            return data

    music = SameArtist(pages=100)
    service = OnlineRecommendationService(AI(choose=25), None, music)
    result = asyncio.run(
        service.soundtrack(
            BOOKS[0], ReadingRequest(book_id=BOOKS[0].id, target_duration_min=90)
        )
    )
    assert len(result["items"]) == 2
    assert result["playlist"]["target_met"] is False


@pytest.mark.parametrize("fail", [False, True])
def test_book_reroll_excludes_all_previously_shown_books_even_without_ai(fail):
    books = Books()
    service = OnlineRecommendationService(
        AI(kind="books", choose=10, fail=fail), books, None
    )
    seen = set()
    for offset in (0, 15, 30):
        result = asyncio.run(
            service.recommend(
                "books",
                BookDiscoveryRequest(
                    query="Fantasia medieval",
                    limit=10,
                    offset=offset,
                    excluded_book_ids=list(seen),
                ),
            )
        )
        ids = {row["item"]["id"] for row in result["items"]}
        assert ids and not ids & seen
        seen.update(ids)
    assert books.offsets == [0, 15, 30]
    assert result["meta"]["next_offset"] is None


def test_local_book_reroll_reaches_exhaustion_without_repeats():
    service = RecommendationService()
    seen = set()
    for _ in range(20):
        result = service.discover(
            "books",
            BookDiscoveryRequest(
                query="fantasia", limit=2, excluded_book_ids=list(seen)
            ),
        )
        ids = {row["item"]["id"] for row in result["items"]}
        assert not ids & seen
        seen.update(ids)
        if not result["meta"]["has_more"]:
            break
    assert seen
    result = service.discover(
        "books", BookDiscoveryRequest(query="fantasia", excluded_book_ids=list(seen))
    )
    assert result["items"] == []
    assert result["meta"]["has_more"] is False


def test_duration_summary_uses_valid_durations_and_marks_estimates():
    rows = [
        {"item": {"duration_ms": 123000}},
        {"item": {"duration_ms": True}},
        {"item": {"duration_ms": -1}},
    ]
    assert reading_summary(rows, 900000) == {
        "tracks_count": 3,
        "total_duration_ms": 723000,
        "duration_estimated": True,
        "target_duration_ms": 900000,
        "target_met": False,
        "shortfall_ms": 177000,
    }


class Store:
    def __init__(self):
        self.calls = 0
        self.cached = None

    def get(self, *args):
        return self.cached

    def put(self, provider, key, limit, data, ttl):
        self.cached = data

    def reserve_ai_call(self, limit):
        if self.calls >= limit:
            return False
        self.calls += 1
        return True


@pytest.mark.parametrize(
    "header,expected_calls",
    [
        ("2", 2),
        ("0", 2),
        ("31", 1),
        ("nan", 1),
        ("inf", 1),
        ("-1", 1),
        ("invalid", 1),
        (None, 1),
    ],
)
def test_groq_retries_only_short_valid_cooldowns_and_counts_each_request(
    monkeypatch, header, expected_calls
):
    calls, sleeps = [], []

    async def sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr("app.ai.groq.asyncio.sleep", sleep)

    def remote(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(
                429, headers={"retry-after": header} if header is not None else {}
            )
        return httpx.Response(
            200, json={"choices": [{"message": {"content": '{"choices": []}'}}]}
        )

    store = Store()

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(remote)) as client:
            ai = GroqClient(
                client, store, Settings(_env_file=None, groq_api_key="test-key")
            )
            if expected_calls == 2:
                assert (await ai.structured(Selection, "test", {})).choices == []
                assert (
                    await ai.structured(Selection, "test", {})
                ).choices == []  # cached
            else:
                with pytest.raises(AppError) as caught:
                    await ai.structured(Selection, "test", {})
                assert caught.value.code == "AI_QUOTA"

    asyncio.run(run())
    assert len(calls) == store.calls == expected_calls
    assert sleeps == ([float(header) + 0.1] if expected_calls == 2 else [])


def test_groq_retry_cannot_bypass_local_daily_allowance(monkeypatch):
    async def sleep(delay):
        pass

    monkeypatch.setattr("app.ai.groq.asyncio.sleep", sleep)
    requests = []

    def remote(request):
        requests.append(request)
        return httpx.Response(429, headers={"retry-after": "0"})

    store = Store()

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(remote)) as client:
            ai = GroqClient(
                client,
                store,
                Settings(_env_file=None, groq_api_key="test-key", ai_daily_limit=1),
            )
            with pytest.raises(AppError) as caught:
                await ai.structured(Selection, "test", {})
            assert caught.value.code == "AI_LOCAL_LIMIT"

    asyncio.run(run())
    assert len(requests) == store.calls == 1
