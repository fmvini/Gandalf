from collections import Counter
from uuid import uuid4

from app.ai.groq import Intent
from app.core.exceptions import AppError
from app.providers.local_catalog import BOOKS, MUSIC, normalize
from app.schemas.recommendation import DiscoveryRequest, MusicFilters
from app.services.music_filters import matches_music_filters, resolve_music_filters
from app.services.recommendation_service import RecommendationService, interpret

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
    def __init__(self, ai, books, music):
        super().__init__()
        self.ai, self.books, self.music = ai, books, music

    async def recommend(self, kind, body):
        return await self._online(kind, body)

    async def _online(self, kind, body):
        warnings = []
        filters = (
            resolve_music_filters(body.query, body.filters)
            if kind == "music"
            else body.filters.model_copy()
        )
        positive, negative = interpret(body.query)
        interpreted_by_ai = False
        try:
            intent = await self.ai.interpret(body.query, kind)
            interpreted_by_ai = True
        except AppError as exc:
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
        intent.themes = list(dict.fromkeys([*intent.themes, *sorted(positive)]))[:8]
        intent.excluded_themes = list(
            dict.fromkeys([*intent.excluded_themes, *sorted(negative)])
        )[:8]
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
                    data = await self.books.discover(term, 15)
                    candidates.extend(
                        item.model_dump(mode="json") for item in data.items
                    )
                else:
                    data = await self.music.search(
                        term, 15, by_tag=bool(intent.search_terms)
                    )
                    candidates.extend(data["items"])
            except AppError as exc:
                warnings.append(exc.message)
        local = (
            MUSIC
            if kind == "music"
            else [book.model_dump(mode="json") for book in BOOKS]
        )
        # Keep a useful local fallback without overwhelming externally retrieved items.
        local_ranked = self.discover(kind, body)["items"]
        candidates = candidates[:18]
        candidates.extend(row["item"] for row in local_ranked[:7])
        if not candidates:
            candidates = list(local)
        unique, seen = [], set()
        for item in candidates:
            key = normalize(
                item["title"]
                + " "
                + item.get("artist", " ".join(item.get("authors", [])))
            )
            if key not in seen:
                seen.add(key)
                unique.append(dict(item))
        candidates = unique[:25]
        choices = None
        if interpreted_by_ai:
            try:
                choices = await self.ai.select(
                    body.query, kind, candidates, filters.model_dump(), body.limit
                )
            except AppError as exc:
                warnings.append(exc.message)
        rows = []
        if choices is not None:
            used, counts = set(), Counter()
            for choice in sorted(choices.choices, key=lambda value: -value.score):
                if (
                    choice.index >= len(candidates)
                    or choice.index in used
                    or choice.score < 0.25
                ):
                    continue
                used.add(choice.index)
                item = dict(candidates[choice.index])
                if any(
                    normalize(item["title"]) == normalize(reference)
                    for reference in intent.references
                ):
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
                if len(rows) >= body.limit:
                    break
        else:
            for item in candidates:
                item["matching_tags"] = metadata_tags(item)
            result = self._rank(
                candidates,
                set(intent.themes) | positive,
                set(intent.excluded_themes) | negative,
                filters,
                body.limit,
                set(),
                intent.references,
            )
            rows = result["items"]
            for row in rows:
                row["explanation"] = row["explanation"].replace(
                    "Classificação editorial do catálogo local.",
                    "Correspondência por regras com os metadados disponíveis.",
                )
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
            },
        }
        return self.remember(result)

    async def soundtrack(self, book, body):
        contexts = {
            "FOCUS": "música calma instrumental para foco",
            "CALM": "música calma",
            "CINEMATIC": "trilha cinematográfica",
            "IMMERSIVE": "música imersiva",
            "CUSTOM": "música",
        }
        filters = MusicFilters(
            vocals="none"
            if body.vocals != "ANY" or body.mode == "FOCUS"
            else "optional",
            energy="low" if body.mode in {"FOCUS", "CALM"} else None,
        )
        query = f"{contexts[body.mode]} para ler {book.title}. Temas: {', '.join(book.subjects[:6])}. {body.context}"
        result = await self._online(
            "music", DiscoveryRequest(query=query[:1000], filters=filters, limit=25)
        )
        target = body.target_duration_min * 60000
        selected, total, estimated = [], 0, False
        for row in result["items"]:
            duration = (
                row["item"].get("duration_ms")
                or row["item"].get("estimated_duration_ms")
                or 300000
            )
            if total >= target:
                break
            estimated |= not bool(row["item"].get("duration_ms"))
            selected.append({**row, "position": len(selected) + 1})
            total += duration
        result["items"] = selected
        result["playlist"] = {
            "total_duration_ms": total,
            "tracks_count": len(selected),
            "duration_estimated": estimated,
        }
        if estimated:
            result["meta"]["hint"] += (
                " Faixas sem duração conhecida são estimadas em 5 minutos."
            )
        if total < target:
            result["meta"]["hint"] += (
                " A seleção disponível não preenche a duração solicitada."
            )
        return result
