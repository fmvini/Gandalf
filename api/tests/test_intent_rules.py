"""Offline regression corpus for the bounded Portuguese rules parser."""

import pytest

from app.schemas.recommendation import DiscoveryRequest
from app.services.recommendation_service import RecommendationService, interpret


@pytest.mark.parametrize(
    "query,positive,negative",
    [
        ("fantasia sem romance", {"fantasia"}, {"romance"}),
        ("fantasia sem romance e terror", {"fantasia"}, {"romance", "terror"}),
        ("aventura sem terror ou romance", {"aventura"}, {"terror", "romance"}),
        ("sem terror nem mistério", set(), {"terror", "mistério"}),
        ("sem romance, terror e política", set(), {"romance", "terror", "política"}),
        ("evite romance e terror", set(), {"romance", "terror"}),
        ("evitar romance e terror", set(), {"romance", "terror"}),
        ("não quero romance e terror", set(), {"romance", "terror"}),
        ("pouco romance e terror", set(), {"romance", "terror"}),
        ("menos tristeza e terror", set(), {"triste", "terror"}),
        ("sem terror. Fantasia", {"fantasia"}, {"terror"}),
        ("sem terror; fantasia", {"fantasia"}, {"terror"}),
        ("sem terror! Fantasia", {"fantasia"}, {"terror"}),
        ("sem terror? Fantasia", {"fantasia"}, {"terror"}),
        ("sem terror\nfantasia", {"fantasia"}, {"terror"}),
        ("sem terror mas fantasia", {"fantasia"}, {"terror"}),
        ("sem terror porém fantasia", {"fantasia"}, {"terror"}),
        ("sem terror contudo fantasia", {"fantasia"}, {"terror"}),
        ("sem terror e quero fantasia", {"fantasia"}, {"terror"}),
        ("sem terror, prefiro fantasia", {"fantasia"}, {"terror"}),
        ("fantasia e aventura", {"fantasia", "aventura"}, set()),
        ("SEM ROMANCE E TERROR, MAS MISTÉRIO", {"mistério"}, {"romance", "terror"}),
        ("romance mas sem romance", set(), {"romance"}),
        ("xyzabcdefgh", set(), set()),
    ],
)
def test_portuguese_exclusion_corpus(query, positive, negative):
    assert interpret(query) == (positive, negative)


@pytest.mark.parametrize("kind", ["books", "music"])
def test_exclusion_lists_reach_ranking_and_explanations(kind):
    service = RecommendationService()
    result = service.discover(
        kind, DiscoveryRequest(query="aventura sem romance e terror", limit=25)
    )
    assert result["items"]
    assert result["parsed_query"]["excluded_themes"] == ["romance", "terror"]
    for row in result["items"]:
        item = row["item"]
        tags = set(item.get("tags", item.get("genres", [])))
        assert "aventura" in tags
        assert not tags & {"romance", "terror"}
        assert (
            "aventura"
            in service.explanation(result["recommendation_id"], str(item["id"]))["text"]
        )
