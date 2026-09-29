import pytest

from app.providers.local_catalog import BOOKS, MUSIC
from app.schemas.recommendation import DiscoveryRequest
from app.services.recommendation_service import RecommendationService
from app.services.references import resolve_references


@pytest.mark.parametrize(
    "query,positive,negative",
    [
        ("Parecidos com Duna", ["Duna"], []),
        ("Parecidos com Dune", ["Duna"], []),
        ("DUNAS e dunedin", [], []),
        ("sem Duna", [], ["Duna"]),
        ("não gostei de Duna", [], ["Duna"]),
        ("sem Duna e O Hobbit", [], ["Duna", "O Hobbit"]),
        ("sem Duna. O Hobbit", ["O Hobbit"], ["Duna"]),
        ("sem Duna mas O Hobbit", ["O Hobbit"], ["Duna"]),
        ("Duna mas não quero Dune", [], ["Duna"]),
        ("O SENHOR DOS ANÉIS", ["O Senhor dos Anéis"], []),
    ],
)
def test_catalog_title_corpus(query, positive, negative):
    source = [book.model_dump(mode="json") for book in BOOKS]
    result = resolve_references(query, source)
    assert result.positive == positive
    assert result.negative == negative
    expected = {item["id"] for item in source if item["title"] in positive + negative}
    assert result.blocked_ids == expected


def test_longest_title_punctuation_and_duplicate_providers():
    source = [
        {"id": "a", "title": "March", "tags": ["short"]},
        {"id": "b", "title": "The Imperial March", "tags": ["epic"]},
        {"id": "c", "title": "The Imperial March", "tags": ["epic"]},
        {"id": "d", "title": "Gymnopédie No. 1", "tags": ["calmo"]},
    ]
    result = resolve_references("Sem The Imperial March. Gymnopédie No. 1", source)
    assert result.blocked_ids == {"b", "c", "d"}
    assert result.positive == ["Gymnopédie No. 1"]
    assert result.tags == {"calmo"}


def test_external_ids_are_not_title_aliases():
    result = resolve_references(
        "OL9999W",
        [
            {
                "id": "one",
                "title": "Example",
                "provider": "open_library",
                "external_id": "OL9999W",
            }
        ],
    )
    assert not result.blocked_ids


@pytest.mark.parametrize("query", ["fantasia sem Duna", "fantasia não gostei de Duna"])
def test_rejected_title_does_not_add_its_themes(query):
    result = RecommendationService().discover("books", DiscoveryRequest(query=query))
    assert result["parsed_query"]["themes"] == ["fantasia"]
    assert result["parsed_query"]["references"] == []
    assert result["parsed_query"]["excluded_references"] == ["Duna"]
    assert result["items"]
    assert all(row["item"]["title"] != "Duna" for row in result["items"])


def test_title_words_are_not_interpreted_as_themes():
    source = [{"id": "one", "title": "Dark Voice", "tags": ["alegre"]}]
    references = resolve_references("como Dark Voice", source)
    assert "dark" not in references.context
    assert references.tags == {"alegre"}


def test_music_partial_word_is_not_a_reference():
    result = resolve_references("quero sobremesa", MUSIC)
    assert "Mesa" not in result.positive
