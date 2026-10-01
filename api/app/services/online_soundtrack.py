"""Build a full reading session from real recordings, independently of AI quota."""

from collections import Counter
from uuid import uuid4

from app.core.exceptions import AppError
from app.providers.local_catalog import normalize
from app.schemas.recommendation import MusicFilters
from app.services.music_filters import matches_music_filters, resolve_music_filters
from app.services.reading_duration import reading_summary
from app.services.recommendation_service import interpret
from app.services.references import resolve_references

PAGE_SIZE = 50
MAX_PAGES = 8
MAX_TRACKS = 60
MAX_PER_ARTIST = 4
CALM_TAGS = {
    "ambient",
    "dark ambient",
    "piano",
    "neo classical",
    "neoclassical",
    "modern classical",
    "minimalism",
    "downtempo",
    "new age",
}
TERM_MAP = {
    "calmo": "ambient",
    "piano": "piano",
    "cinematográfico": "soundtrack",
    "sombrio": "dark ambient",
    "jazz": "jazz",
    "clássica": "classical",
}


async def generate_soundtrack(ai, music, book, body):
    # A book's genre must not replace the user's requested musical atmosphere.
    request = f"Música para leitura, modo {body.mode}. {body.context}"
    query = request + f". Livro: {book.title[:150]}."
    positive, negative = interpret(body.context)
    filters = resolve_music_filters(
        body.context,
        MusicFilters(
            vocals="none" if body.vocals != "ANY" or body.mode == "FOCUS" else None,
        ),
    )
    if filters.vocals is None:
        filters.vocals = "optional"
    warnings = []
    intent = None
    try:
        intent = await ai.interpret(query, "music")
    except AppError as exc:
        warnings.append(exc.message)
    terms = [TERM_MAP[tag] for tag in sorted(positive) if tag in TERM_MAP]
    if not terms:
        terms = (
            ["ambient", "piano"]
            if body.mode in {"FOCUS", "CALM", "CUSTOM"}
            else ["soundtrack", "ambient"]
        )
    if any(word in normalize(body.context) for word in ["drama", "historia", "cinema"]):
        terms.append("soundtrack")
    if intent is not None:
        terms.extend(intent.search_terms)
    # Choose broad catalog tags; never send the complete prose as a song title.
    terms = list(dict.fromkeys(term.strip()[:120] for term in terms if term.strip()))[
        :3
    ]
    terms = [term for term in terms if not (interpret(term)[0] & negative)]
    if not terms:
        raise AppError(
            422,
            "VALIDATION_ERROR",
            "Os estilos musicais pedidos também foram excluídos. Revise o contexto.",
        )
    target = body.target_duration_min * 60000
    selected, seen = [], set()
    seen_ids = set()
    counts = Counter()
    total = 0
    ai_used = False
    selection_attempted = False
    pages = 0
    for page in range(MAX_PAGES):
        candidates = []
        has_more = False
        for term in terms:
            try:
                data = await music.search(
                    term,
                    PAGE_SIZE,
                    by_tag=True,
                    offset=page * PAGE_SIZE,
                    reading=True,
                    instrumental=filters.vocals == "none",
                )
                candidates.extend(data["items"])
                has_more |= data.get("has_more", False)
            except AppError as exc:
                warnings.append(exc.message)
        pages += 1
        references = resolve_references(body.context, candidates)
        blocked = references.blocked_ids
        unique = {}
        unique_ids = set()
        for raw in candidates:
            item = dict(raw)
            duration = item.get("duration_ms")
            if (
                item.get("provider") != "musicbrainz"
                or type(duration) is not int
                or not 90000 <= duration <= 600000
            ):
                continue
            key = (normalize(item["title"]), normalize(item["artist"]))
            if (
                key in seen
                or item["id"] in seen_ids
                or item["id"] in unique_ids
                or item["id"] in blocked
            ):
                continue
            tags = {normalize(tag) for tag in item.get("tags", [])}
            if "instrumental" in tags:
                item["has_vocals"] = False
            known_themes, _ = interpret(" ".join(tags))
            if known_themes & negative or "vocal" in tags and filters.vocals == "none":
                continue
            # Tag-based atmosphere is a preference, not a measured energy claim.
            item["energy"] = "low" if tags & CALM_TAGS else item.get("energy")
            if not matches_music_filters(
                item.get("has_vocals"), item.get("energy"), filters
            ):
                continue
            if body.mode == "FOCUS" and tags & {
                "metal",
                "heavy metal",
                "punk",
                "hard rock",
                "techno",
            }:
                continue
            score = len(known_themes & positive) + (
                2 if tags & CALM_TAGS and body.mode in {"FOCUS", "CALM"} else 0
            )
            if key not in unique:
                unique[key] = (item, score)
                unique_ids.add(item["id"])
        ranked = list(unique.values())
        # AI orders a small sample once; omissions must never limit playlist length.
        if ranked and intent is not None and not selection_attempted:
            selection_attempted = True
            try:
                choices = await ai.select(
                    query,
                    "music",
                    [item for item, _ in ranked[:25]],
                    filters.model_dump(),
                    25,
                    target_duration_ms=target - total,
                )
                ai_used = True
                chosen_indices = set()
                for choice in choices.choices:
                    if choice.index in chosen_indices:
                        continue
                    chosen_indices.add(choice.index)
                    if choice.index < min(25, len(ranked)) and choice.score >= 0.25:
                        item, score = ranked[choice.index]
                        if (choice.vocals == "vocal" and filters.vocals == "none") or (
                            filters.energy
                            and choice.energy not in {filters.energy, "unknown"}
                        ):
                            ranked[choice.index] = (None, -1)
                        else:
                            ranked[choice.index] = (item, score + choice.score)
            except AppError as exc:
                warnings.append(exc.message)
        ranked = [(item, score) for item, score in ranked if item is not None]
        ranked.sort(key=lambda row: (-row[1], row[0]["title"].casefold()))
        for item, score in ranked:
            artist = normalize(item["artist"])
            key = (normalize(item["title"]), artist)
            if counts[artist] >= MAX_PER_ARTIST or key in seen:
                continue
            seen.add(key)
            seen_ids.add(item["id"])
            counts[artist] += 1
            selected.append(
                {
                    "position": len(selected) + 1,
                    "item": item,
                    "scores": {"context": min(1.0, score / 4)},
                    "explanation": "Gravação real encontrada no MusicBrainz, com duração informada pela fonte. "
                    + (
                        "A fonte identifica a faixa como instrumental. "
                        if item.get("has_vocals") is False
                        else ""
                    )
                    + "Afinidade por temas e atmosfera; não é uma medição acústica.",
                }
            )
            total += item["duration_ms"]
            if total >= target or len(selected) >= MAX_TRACKS:
                break
        if total >= target or len(selected) >= MAX_TRACKS or not has_more:
            break
    if total < target:
        raise AppError(
            503,
            "SOUNDTRACK_INCOMPLETE",
            f"Não foi possível montar {body.target_duration_min} minutos de faixas reais com os filtros pedidos nesta tentativa. "
            f"A fonte forneceu {len(selected)} faixas compatíveis ({total // 60000} minutos). Tente novamente ou ajuste o contexto musical.",
        )
    return {
        "recommendation_id": str(uuid4()),
        "parsed_query": {"search_terms": terms, **filters.model_dump()},
        "items": selected,
        "playlist": reading_summary(selected, target),
        "meta": {
            "mode": "online",
            "ai_used": ai_used,
            "degraded": bool(warnings),
            "sources": ["musicbrainz"],
            "retrieval_rounds": pages,
            "hint": "Faixas reais com duração informada pelo MusicBrainz; sem durações estimadas. "
            + (
                "IA usada na ordenação. "
                if ai_used
                else "Ordenação por temas e atmosfera. "
            )
            + " ".join(dict.fromkeys(warnings)),
        },
    }
