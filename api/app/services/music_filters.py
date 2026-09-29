"""Deterministic music constraints shared by local and online ranking."""

import re

from app.core.exceptions import AppError
from app.providers.local_catalog import normalize
from app.schemas.recommendation import MusicFilters

MENTION = re.compile(
    r"\b(?:instrumental|instrumentais|voz|vozes|vocal|vocais|letra|letras|"
    r"energia (?:baixa|media|alta)|(?:baixa|media|alta) energia)\b"
)
NEGATION = re.compile(r"\b(?:sem|nao quero|nao|evitar|evite)(?: \w+){0,2}$")
ENERGY = {"baixa": "low", "media": "medium", "alta": "high"}


def resolve_music_filters(query: str, explicit: MusicFilters) -> MusicFilters:
    vocals, energies, excluded = set(), set(), set()
    for clause in re.split(r"[.!?;:\n]+", query):
        for text in re.split(r"\b(?:mas|porem|contudo)\b", normalize(clause)):
            end, previous_negative = 0, False
            for match in MENTION.finditer(text):
                bridge = text[end : match.start()].strip()
                negative = bool(
                    NEGATION.search(bridge)
                    or (
                        previous_negative
                        and re.fullmatch(r"(?:(?:e|ou|nem)\s*)*", bridge)
                    )
                )
                value = match.group()
                if "energia" in value:
                    energy = ENERGY[value.replace("energia", "").strip()]
                    (excluded if negative else energies).add(energy)
                else:
                    instrumental = value in {"instrumental", "instrumentais"}
                    vocals.add("none" if instrumental != negative else "required")
                end, previous_negative = match.end(), negative

    result = explicit.model_copy(deep=True)
    if explicit.vocals is None:
        if len(vocals) > 1:
            raise AppError(
                422,
                "VALIDATION_ERROR",
                "O pedido mistura músicas com e sem voz. Escolha um filtro de voz.",
            )
        result.vocals = next(iter(vocals), None)
    # An explicit energy selection replaces the entire inferred energy constraint.
    if explicit.energy is None and "excluded_energy" not in explicit.model_fields_set:
        if len(energies) > 1 or energies & excluded:
            raise AppError(
                422,
                "VALIDATION_ERROR",
                "O pedido contém níveis de energia conflitantes. Escolha um filtro de energia.",
            )
        result.energy = next(iter(energies), None)
        result.excluded_energy = sorted(excluded)
    return result


def matches_music_filters(
    vocals: bool | None, energy: str | None, filters: MusicFilters
) -> bool:
    if filters.vocals == "none" and vocals is not False:
        return False
    if filters.vocals == "required" and vocals is not True:
        return False
    if filters.energy and energy != filters.energy:
        return False
    return not (
        filters.excluded_energy
        and (energy is None or energy in filters.excluded_energy)
    )
