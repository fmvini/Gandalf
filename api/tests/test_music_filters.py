import pytest

from app.core.exceptions import AppError
from app.schemas.recommendation import MusicFilters
from app.services.music_filters import resolve_music_filters


@pytest.mark.parametrize(
    "query,vocals,energy,excluded",
    [
        ("instrumental", "none", None, []),
        ("instrumentais", "none", None, []),
        ("sem voz", "none", None, []),
        ("sem vozes", "none", None, []),
        ("sem vocais", "none", None, []),
        ("sem letras", "none", None, []),
        ("não quero vocais", "none", None, []),
        ("evite voz", "none", None, []),
        ("com voz", "required", None, []),
        ("com vocais", "required", None, []),
        ("não quero instrumental", "required", None, []),
        ("sem instrumentais", "required", None, []),
        ("evitar instrumental", "required", None, []),
        ("energia média", None, "medium", []),
        ("alta energia", None, "high", []),
        ("energia baixa", None, "low", []),
        ("sem energia alta", None, None, ["high"]),
        ("não quero baixa energia", None, None, ["low"]),
        ("evite energia média", None, None, ["medium"]),
        ("sem energia alta nem energia média", None, None, ["high", "medium"]),
        ("sem voz. Energia alta", "none", "high", []),
        ("sem vocais mas energia média", "none", "medium", []),
        ("instrumental sem energia alta", "none", None, ["high"]),
        ("energia baixa sem energia alta", None, "low", ["high"]),
        ("instrumentalização e vozerio", None, None, []),
        ("aventura", None, None, []),
    ],
)
def test_music_constraint_corpus(query, vocals, energy, excluded):
    result = resolve_music_filters(query, MusicFilters())
    assert result.model_dump() == {
        "vocals": vocals,
        "energy": energy,
        "excluded_energy": excluded,
    }


@pytest.mark.parametrize(
    "query",
    [
        "instrumental com voz",
        "energia baixa e energia alta",
        "energia alta sem energia alta",
    ],
)
def test_conflicting_text_requires_a_choice(query):
    with pytest.raises(AppError) as exc:
        resolve_music_filters(query, MusicFilters())
    assert exc.value.status_code == 422


def test_explicit_constraints_override_only_their_dimension():
    explicit = MusicFilters(vocals="optional", energy="high")
    result = resolve_music_filters("instrumental com voz sem energia alta", explicit)
    assert result == explicit
    assert resolve_music_filters(
        "sem voz e energia alta", MusicFilters(excluded_energy=[])
    ) == MusicFilters(vocals="none")
    assert resolve_music_filters(
        "energia baixa sem voz", MusicFilters(excluded_energy=["high"])
    ) == MusicFilters(vocals="none", excluded_energy=["high"])
