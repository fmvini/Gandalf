import re
from collections import Counter, OrderedDict
from math import ceil
from time import monotonic
from uuid import uuid4

from app.core.exceptions import AppError
from app.providers.local_catalog import BOOKS, MUSIC, normalize
from app.schemas.book import BookItem
from app.schemas.recommendation import DiscoveryRequest, MusicFilters, ReadingRequest
from app.services.music_filters import matches_music_filters, resolve_music_filters
from app.services.references import resolve_references

RANKING_VERSION = "local-rules-v3"
CATALOG_NOTE = "Catálogo local selecionado. Sugestões por temas e filtros, sem IA paga."
ALIASES = {
    "calmo": (
        "calm",
        "tranquil",
        "relax",
        "dormir",
        "sono",
        "chuva",
        "estudar",
        "foco",
        "concentr",
        "discret",
    ),
    "acolhedor": ("acolhed", "cozy", "confort", "aconcheg"),
    "triste": ("trist", "melancol", "saudade"),
    "alegre": ("alegr", "feliz", "animad", "dancar", "treinar"),
    "atmosférico": ("atmosfer", "ambient", "espacial"),
    "introspectivo": ("introspec", "intimist", "reflex", "pensar"),
    "fantasia": (
        "fantasia",
        "fantasy",
        "magia",
        "medieval",
        "construcao de mundo",
        "terra media",
    ),
    "ficção científica": (
        "ficcao cientifica",
        "sci fi",
        "science fiction",
        "espaco",
        "futur",
    ),
    "mistério": ("mister", "suspense", "detetive", "investig"),
    "sombrio": ("sombri", "escur", "dark"),
    "terror": ("terror", "horror", "medo"),
    "romance": ("romance", "romantic", "amor"),
    "aventura": ("aventur", "explor"),
    "viagem": ("viagem", "viajar", "viajando", "estrada"),
    "épico": ("epic", "grandios", "batalha"),
    "cinematográfico": ("cinema", "filme", "trilha sonora", "orquestr"),
    "esperançoso": ("esperanc", "otimist", "inspir"),
    "política": ("politic", "imperio", "sociedade"),
    "deserto": ("deserto", "arrakis", "areia"),
    "cyberpunk": ("cyberpunk", "ciberpunk"),
}


def interpret(query: str) -> tuple[set[str], set[str]]:
    positive, negative = set(), set()
    # Preserve clause boundaries before normalization removes punctuation.
    for clause in re.split(r"[.!?;:\n]+", query):
        for text in re.split(r"\b(?:mas|porem|contudo)\b", normalize(clause)):
            matches = sorted(
                (match.start(), match.end(), tag)
                for tag, aliases in ALIASES.items()
                for alias in aliases
                for match in re.finditer(r"\b" + re.escape(alias) + r"\w*", text)
            )
            last_end, last_excluded = 0, False
            for start, end, tag in matches:
                if start < last_end:
                    continue
                bridge = text[last_end:start].strip()
                # Carry negation only across a list, never arbitrary intervening text.
                continuation = re.fullmatch(r"(?:(?:e|ou|nem)\s*)*", bridge)
                explicit = re.search(
                    r"\b(?:sem|evitar|evite|nao quero|pouco|pouca|menos)"
                    r"(?: \w+){0,2}$",
                    bridge,
                )
                excluded = bool(explicit or (last_excluded and continuation))
                (negative if excluded else positive).add(tag)
                last_end, last_excluded = end, excluded
    return positive - negative, negative


class RecommendationService:
    def __init__(self):
        # Anonymous results are private by unguessable ID, expire in one hour,
        # and are bounded to avoid retaining unbounded user queries in memory.
        self.results: OrderedDict[str, tuple[float, dict]] = OrderedDict()

    async def recommend(self, kind, body):
        return self.discover(kind, body)

    async def soundtrack(self, book, body):
        return self.reading(book, body)

    def discover(self, kind: str, body: DiscoveryRequest) -> dict:
        source = (
            MUSIC
            if kind == "music"
            else [book.model_dump(mode="json") for book in BOOKS]
        )
        references = resolve_references(body.query, source)
        positive, negative = interpret(references.context)
        positive.update(references.tags)
        positive -= negative
        filters = body.filters.model_copy()
        if kind == "music":
            filters = resolve_music_filters(references.context, body.filters)
        result = self._rank(
            source,
            positive,
            negative,
            filters,
            body.limit,
            references.blocked_ids,
            references.positive,
        )
        result["parsed_query"]["excluded_references"] = references.negative
        return result

    def reading(self, book: BookItem, body: ReadingRequest) -> dict:
        positive, negative = interpret(body.context)
        book_tags, _ = interpret(" ".join([book.title, *book.subjects, *book.genres]))
        positive.update(book_tags)
        filters = MusicFilters()
        if body.vocals != "ANY" or body.mode == "FOCUS":
            # MINIMAL conservatively selects instrumentals: no invented vocal ratio.
            filters.vocals = "none"
        if body.mode in {"FOCUS", "CALM"}:
            positive.add("calmo")
            filters.energy = "low"
        elif body.mode == "CINEMATIC":
            positive.add("cinematográfico")
        result = self._rank(
            MUSIC,
            positive - negative,
            negative,
            filters,
            ceil(body.target_duration_min / 5),
            set(),
            [book.title],
        )
        total = sum(row["item"]["estimated_duration_ms"] for row in result["items"])
        result["playlist"] = {
            "total_duration_ms": total,
            "tracks_count": len(result["items"]),
            "duration_estimated": True,
        }
        result["meta"]["hint"] += (
            " Duração estimada em 5 minutos por faixa; varia conforme a gravação."
        )
        if total < body.target_duration_min * 60_000:
            result["meta"]["hint"] += (
                " O catálogo disponível não preenche toda a duração solicitada."
            )
        return result

    def _rank(
        self, source, positive, negative, filters, limit, reference_ids, references
    ):
        candidates = []
        for item in source:
            tags = set(
                item.get("matching_tags", item.get("tags", item.get("genres", [])))
            )
            if tags & negative or item["id"] in reference_ids:
                continue
            if "has_vocals" in item and not matches_music_filters(
                item["has_vocals"], item.get("energy"), filters
            ):
                continue
            matched = tags & positive
            if not matched and positive:
                continue
            if (
                not positive
                and not negative
                and not filters.vocals
                and not filters.energy
                and not filters.excluded_energy
            ):
                continue
            score = len(matched) / max(len(positive), 1)
            candidates.append((score, item, sorted(matched)))
        candidates.sort(key=lambda row: (-row[0], row[1]["title"]))
        counts = Counter()
        rows = []
        for score, item, matched in candidates:
            creator = item.get("artist", ", ".join(item.get("authors", [])))
            if counts[creator] >= 2:
                continue
            counts[creator] += 1
            reasons = (
                "Temas em comum: " + ", ".join(matched) + "."
                if matched
                else "Atende aos filtros solicitados."
            )
            if filters.vocals == "none":
                reasons += " Seleção instrumental."
            if filters.vocals == "required":
                reasons += " Seleção com voz."
            if filters.energy:
                reasons += (
                    " Energia "
                    + {"low": "baixa", "medium": "média", "high": "alta"}[
                        filters.energy
                    ]
                    + "."
                )
            if filters.excluded_energy:
                labels = {"low": "baixa", "medium": "média", "high": "alta"}
                reasons += (
                    " Exclui energia "
                    + ", ".join(labels[value] for value in filters.excluded_energy)
                    + "."
                )
            rows.append(
                {
                    "position": len(rows) + 1,
                    "item": dict(item),
                    "scores": {"context": round(score, 4)},
                    "explanation": reasons
                    + " Classificação editorial do catálogo local.",
                }
            )
            if len(rows) >= limit:
                break
        result = {
            "recommendation_id": str(uuid4()),
            "parsed_query": {
                "themes": sorted(positive),
                "excluded_themes": sorted(negative),
                "references": references,
                **filters.model_dump(exclude_none=True),
            },
            "items": rows,
            "meta": {
                "mode": "local",
                "ranking_version": RANKING_VERSION,
                "hint": CATALOG_NOTE
                if rows
                else "Nenhuma opção no catálogo local para esse pedido. Tente fantasia, mistério, calma, aventura ou amplie os filtros.",
            },
        }
        return self.remember(result)

    def remember(self, result):
        self._prune()
        self.results[result["recommendation_id"]] = (monotonic() + 3600, result)
        while len(self.results) > 256:
            self.results.popitem(last=False)
        return result

    def _prune(self):
        now = monotonic()
        for key in [key for key, (expiry, _) in self.results.items() if expiry <= now]:
            del self.results[key]

    def explanation(self, recommendation_id: str, item_id: str) -> dict:
        self._prune()
        record = self.results.get(recommendation_id)
        if record:
            for row in record[1]["items"]:
                if row["item"]["id"] == item_id:
                    return {"text": row["explanation"]}
        raise AppError(
            404,
            "NOT_FOUND",
            "Sugestão não encontrada ou expirada. Faça uma nova busca.",
        )
