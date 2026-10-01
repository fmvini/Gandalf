"""Verified translation aliases for gaps in the external edition index.

These are lookup aliases, not book records: results still come from Open Library.
Do not translate titles speculatively or apply an alias to a different author.
"""

from app.providers.local_catalog import normalize

# Brazilian publisher confirms the original title and author:
# https://www.intrinseca.com.br/upload/livros/1%C2%BACAP%20QuemEVoceAlasca.pdf
ALIASES = (("Looking for Alaska", "Quem é você, Alasca?", "John Green"),)


def lookup_alias(title: str) -> tuple[str, str, str] | None:
    key = normalize(title)
    return next(
        (
            entry
            for entry in ALIASES
            if key in {normalize(entry[0]), normalize(entry[1])}
        ),
        None,
    )


def translated_title(title: str, authors: list[str]) -> str | None:
    key = normalize(title)
    return next(
        (
            portuguese
            for original, portuguese, author in ALIASES
            if key == normalize(original)
            and normalize(author) in {normalize(value) for value in authors}
        ),
        None,
    )
