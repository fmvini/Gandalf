"""Cover normalization only: no network, database updates or live API restart."""

from uuid import NAMESPACE_URL, uuid5

import pytest

from app.providers.open_library import normalize_book


def work(work_cover, edition_cover):
    return {
        "key": "/works/OL17365W",
        "title": "2001: A Space Odyssey",
        "author_name": ["Arthur C. Clarke"],
        "cover_i": work_cover,
        "editions": {
            "docs": [
                {
                    "key": "/books/OL123M",
                    "title": "2001: Uma Odisseia no Espaço",
                    "language": ["por"],
                    "cover_i": edition_cover,
                }
            ]
        },
    }


@pytest.mark.parametrize("edition_cover", [None, 0, -1, True, False, "456", 1.5])
def test_invalid_portuguese_cover_preserves_valid_work_cover_and_identity(
    edition_cover,
):
    book = normalize_book(work(123, edition_cover))
    assert (
        book.cover_url == "https://covers.openlibrary.org/b/id/123-M.jpg?default=false"
    )
    assert book.id == uuid5(NAMESPACE_URL, "https://openlibrary.org/works/OL17365W")
    assert book.external_id == "OL17365W"
    assert book.external_url == "https://openlibrary.org/works/OL17365W"
    assert book.title == "2001: Uma Odisseia no Espaço"
    assert book.authors == ["Arthur C. Clarke"]
    assert book.provider == "open_library"


@pytest.mark.parametrize("work_cover", [None, 0, -1, True, "123", 123])
def test_valid_portuguese_cover_takes_precedence_and_json_shape_is_unchanged(
    work_cover,
):
    book = normalize_book(work(work_cover, 456))
    assert (
        book.cover_url == "https://covers.openlibrary.org/b/id/456-M.jpg?default=false"
    )
    payload = book.model_dump(mode="json")
    assert payload["cover_url"] == book.cover_url
    assert payload["id"] == str(book.id)
    assert set(payload) == {
        "id",
        "title",
        "authors",
        "description",
        "genres",
        "subjects",
        "publication_year",
        "cover_url",
        "external_url",
        "provider",
        "external_id",
    }


@pytest.mark.parametrize("cover", [None, 0, -1, True, False, "123", 1.5])
def test_without_valid_cover_returns_json_null_and_preserves_portuguese_title(cover):
    book = normalize_book(work(cover, cover))
    assert book.cover_url is None
    assert book.model_dump(mode="json")["cover_url"] is None
    assert book.title == "2001: Uma Odisseia no Espaço"


def test_no_portuguese_edition_keeps_work_metadata_and_https_cover():
    raw = work(123, 456)
    raw.pop("editions")
    book = normalize_book(raw)
    assert book.title == raw["title"]
    assert book.authors == raw["author_name"]
    assert (
        book.cover_url == "https://covers.openlibrary.org/b/id/123-M.jpg?default=false"
    )


def test_missing_edition_cover_field_falls_back_to_work():
    raw = work(123, None)
    del raw["editions"]["docs"][0]["cover_i"]
    book = normalize_book(raw)
    assert (
        book.cover_url == "https://covers.openlibrary.org/b/id/123-M.jpg?default=false"
    )
