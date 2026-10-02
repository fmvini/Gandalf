from collections import Counter
from uuid import uuid4

from starlette.concurrency import run_in_threadpool

from app.ai.groq import Intent
from app.core.exceptions import AppError
from app.providers.local_catalog import BOOKS, MUSIC, normalize
from app.services.music_filters import matches_music_filters, resolve_music_filters
from app.services.online_soundtrack import generate_soundtrack
from app.services.recommendation_service import RecommendationService, interpret
from app.services.references import resolve_references


def item_key(item):
    return normalize(
        item["title"] + " " + item.get("artist", " ".join(item.get("authors", [])))
    )


ENGLISH = {
    "calmo": "ambient",
    "acolhedor": "cozy",
    "triste": "melancholic",
    "alegre": "pop",
    "atmosférico": "ambient",
    "introspectivo": "contemporary",
    "fantasia": "fantasy",
    "ficção científica": "science fiction",
    "mistério": "mystery",
    "detetive": "detective fiction",
    "piano": "piano",
    "sombrio": "dark ambient",
    "terror": "horror",
    "romance": "romance",
    "aventura": "adventure",
    "viagem": "travel",
    "épico": "epic",
    "cinematográfico": "soundtrack",
    "esperançoso": "inspirational",
    "política": "politics",
    "deserto": "desert",
    "cyberpunk": "cyberpunk",
}


def metadata_tags(item):
    raw = item.get("tags", item.get("subjects", []))
    tags, _ = interpret(" ".join(raw))
    for tag, english in ENGLISH.items():
        if any(english in normalize(value) for value in raw):
            tags.add(tag)
    return sorted(tags)


class OnlineRecommendationService(RecommendationService):
    def __init__(self, ai, books, music, cache=None):
        super().__init__(cache)
        self.ai, self.books, self.music = ai, books, music

    async def recommend(self, kind, body):
        exclusion_field = (
            "excluded_music_ids" if kind == "music" else "excluded_book_ids"
        )
        return await self._online(
            kind,
            body,
            excluded_ids={str(value) for value in getattr(body, exclusion_field, [])},
            offset=getattr(body, "offset", 0),
        )

    async def _online(
        self,
        kind,
        body,
        *,
        excluded_ids=None,
        excluded_keys=None,
        offset=0,
        artist_counts=None,
        target_duration_ms=None,
        intent_cache=None,
    ):
        warnings = []
        excluded_ids = excluded_ids or set()
        excluded_keys = excluded_keys or set()
        artist_counts = artist_counts or Counter()
        catalog_has_more = False
        local = (
            MUSIC
            if kind == "music"
            else [book.model_dump(mode="json") for book in BOOKS]
        )
        local_references = resolve_references(body.query, local)
        filters = (
            resolve_music_filters(local_references.context, body.filters)
            if kind == "music"
            else body.filters.model_copy()
        )
        positive, negative = interpret(local_references.context)
        positive.update(local_references.tags)
        positive -= negative
        interpreted_by_ai = False
        try:
            if intent_cache is not None and "error" in intent_cache:
                raise intent_cache["error"]
            if intent_cache is not None and "intent" in intent_cache:
                intent = intent_cache["intent"].model_copy(deep=True)
            else:
                intent = await self.ai.interpret(body.query, kind)
                if intent_cache is not None:
                    intent_cache["intent"] = intent.model_copy(deep=True)
            interpreted_by_ai = True
        except AppError as exc:
            if intent_cache is not None:
                intent_cache["error"] = exc
            warnings.append(exc.message)
            intent = Intent(
                search_terms=list(
                    dict.fromkeys(ENGLISH[tag] for tag in sorted(positive))
                )[:2],
                themes=sorted(positive),
                excluded_themes=sorted(negative),
                references=[],
                vocals="optional",
                energy="any",
            )
        if kind == "music":
            if filters.vocals is None:
                filters.vocals = intent.vocals
            if (
                filters.energy is None
                and not filters.excluded_energy
                and "excluded_energy" not in body.filters.model_fields_set
                and intent.energy != "any"
            ):
                filters.energy = intent.energy
        terms = [term[:120] for term in intent.search_terms if term.strip()][:2]
        if not terms:
            terms = [body.query[:180]]
        candidates = []
        for term in terms:
            try:
                if kind == "books":
                    data = await self.books.discover(term, 15, offset=offset)
                    catalog_has_more |= data.total > offset + 15
                    candidates.extend(
                        item.model_dump(mode="json") for item in data.items
                    )
                else:
                    data = await self.music.search(
                        term,
                        15,
                        by_tag=bool(intent.search_terms),
                        **({"offset": offset} if offset else {}),
                    )
                    catalog_has_more |= data.get("has_more", len(data["items"]) >= 15)
                    candidates.extend(data["items"])
            except AppError as exc:
                warnings.append(exc.message)
        references = resolve_references(body.query, [*local, *candidates])
        blocked_ids = references.blocked_ids | excluded_ids
        positive, negative = interpret(references.context)
        reference_tags, _ = interpret(" ".join(references.tags))
        positive = (positive | reference_tags) - negative
        intent.themes = sorted(
            positive | (set(intent.themes) if interpreted_by_ai else set())
        )
        intent.excluded_themes = sorted(
            negative | (set(intent.excluded_themes) if interpreted_by_ai else set())
        )
        # Keep a useful local fallback without treating words inside titles as genres.
        local_ranked = self._rank(
            local,
            positive,
            negative,
            filters,
            body.limit,
            blocked_ids,
            references.positive,
        )["items"]
        candidates = [
            item
            for item in candidates
            if str(item["id"]) not in blocked_ids
            and item_key(item) not in excluded_keys
            and artist_counts[item.get("artist", "")] < 2
        ][:18]
        candidates.extend(row["item"] for row in local_ranked[:7])
        if not candidates:
            candidates = list(local)
        unique, seen, seen_ids = [], set(), set()
        for item in candidates:
            key = item_key(item)
            if (
                str(item["id"]) in blocked_ids
                or key in excluded_keys
                or artist_counts[item.get("artist", "")] >= 2
            ):
                continue
            if key not in seen and str(item["id"]) not in seen_ids:
                seen.add(key)
                seen_ids.add(str(item["id"]))
                unique.append(dict(item))
        candidates = unique[:25]
        # Probe one extra compatible result without another provider/AI call.
        selection_limit = min(body.limit + 1, 25)
        choices = None
        if interpreted_by_ai and candidates:
            try:
                if intent_cache is not None and "selection_quota" in intent_cache:
                    raise intent_cache["selection_quota"]
                choices = await self.ai.select(
                    body.query,
                    kind,
                    candidates,
                    filters.model_dump(),
                    selection_limit,
                    **(
                        {"target_duration_ms": target_duration_ms}
                        if target_duration_ms is not None
                        else {}
                    ),
                )
            except AppError as exc:
                if intent_cache is not None and exc.code in {
                    "AI_QUOTA",
                    "AI_LOCAL_LIMIT",
                }:
                    intent_cache["selection_quota"] = exc
                warnings.append(exc.message)
        rows = []
        if choices is not None:
            used, counts = set(), Counter(artist_counts)
            for choice in sorted(choices.choices, key=lambda value: -value.score):
                if (
                    choice.index >= len(candidates)
                    or choice.index in used
                    or choice.score < 0.25
                ):
                    continue
                used.add(choice.index)
                item = dict(candidates[choice.index])
                if str(item["id"]) in blocked_ids:
                    continue
                known_tags = set(metadata_tags(item))
                if known_tags & (set(intent.excluded_themes) | negative):
                    continue
                if kind == "music":
                    vocals = item.get("has_vocals")
                    energy = item.get("energy")
                    inferred = item.get("provider") == "musicbrainz"
                    if vocals is None:
                        vocals = {"instrumental": False, "vocal": True}.get(
                            choice.vocals
                        )
                    if energy is None:
                        energy = None if choice.energy == "unknown" else choice.energy
                    if not matches_music_filters(vocals, energy, filters):
                        continue
                    item.update(has_vocals=vocals, energy=energy)
                    if inferred:
                        item["classification_source"] = "ai_estimate"
                creator = item.get("artist", ", ".join(item.get("authors", [])))
                if counts[creator] >= 2:
                    continue
                counts[creator] += 1
                rows.append(
                    {
                        "position": len(rows) + 1,
                        "item": item,
                        "scores": {"context": choice.score},
                        "explanation": "A IA estimou afinidade com seu pedido ao comparar título, autoria e temas disponíveis. "
                        + (
                            "Temas informados: "
                            + ", ".join(item.get("tags", item.get("subjects", []))[:5])
                            + ". "
                            if item.get("tags", item.get("subjects", []))
                            else "A fonte não informou temas detalhados. "
                        )
                        + (
                            "Energia e vocais são estimativas, não medições."
                            if kind == "music"
                            else "A ausência de um tema nos metadados não garante sua ausência na obra."
                        ),
                    }
                )
                if len(rows) >= selection_limit:
                    break
        else:
            for item in candidates:
                item["matching_tags"] = metadata_tags(item)
            result = self._rank(
                candidates,
                set(intent.themes) | positive,
                set(intent.excluded_themes) | negative,
                filters,
                selection_limit,
                blocked_ids,
                references.positive,
            )
            rows = result["items"]
            if artist_counts:
                counts = Counter(artist_counts)
                accepted = []
                for row in rows:
                    artist = row["item"].get("artist", "")
                    if counts[artist] < 2:
                        counts[artist] += 1
                        accepted.append({**row, "position": len(accepted) + 1})
                rows = accepted
            for row in rows:
                row["explanation"] = row["explanation"].replace(
                    "Classificação editorial do catálogo local.",
                    "Correspondência por regras com os metadados disponíveis.",
                )
        page_has_more = len(rows) > body.limit
        rows = rows[: body.limit]
        next_offset = offset + 15 if catalog_has_more and offset + 15 <= 300 else None
        can_continue = len(excluded_ids) < 200
        sources = sorted({row["item"].get("provider", "local") for row in rows})
        hint = (
            "Pedido interpretado e sugestões ordenadas por IA."
            if choices is not None
            else "Sugestões classificadas por regras."
        )
        if "musicbrainz" in sources:
            hint += " Metadados: MusicBrainz. Energia e vocais estimados pela IA quando informados."
        if "open_library" in sources:
            hint += " Livros encontrados na Open Library."
        if "local" in sources:
            hint += " Inclui seleção do catálogo local."
        if not rows:
            hint += " Nenhum item compatível; tente ampliar os filtros."
        if warnings:
            hint += " " + " ".join(dict.fromkeys(warnings))
        result = {
            "recommendation_id": str(uuid4()),
            "parsed_query": {
                **intent.model_dump(),
                "references": references.positive,
                "excluded_references": references.negative,
                **filters.model_dump(exclude_none=True),
                **({"energy": filters.energy or "any"} if kind == "music" else {}),
            },
            "items": rows,
            "meta": {
                "mode": "online",
                "ai_used": choices is not None,
                "degraded": bool(warnings),
                "sources": sources,
                "hint": hint,
                **(
                    {
                        "has_more": can_continue
                        and (page_has_more or next_offset is not None),
                        "next_offset": next_offset if can_continue else None,
                    }
                    if target_duration_ms is None
                    else {}
                ),
                **(
                    {
                        "catalog_has_more": catalog_has_more,
                        "warnings": list(dict.fromkeys(warnings)),
                    }
                    if target_duration_ms is not None
                    else {}
                ),
            },
        }
        if self.cache is None:
            return self.remember(result)
        return await run_in_threadpool(self.remember, result)

    async def soundtrack(self, book, body):
        result = await generate_soundtrack(self.ai, self.music, book, body)
        if self.cache is None:
            return self.remember(result)
        return await run_in_threadpool(self.remember, result)
