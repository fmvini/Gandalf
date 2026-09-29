"""Resolve only titles present in the query and in the available catalog."""

import re
import unicodedata
from dataclasses import dataclass, field

from app.providers.local_catalog import normalize


@dataclass
class References:
    positive: list[str] = field(default_factory=list)
    negative: list[str] = field(default_factory=list)
    blocked_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    context: str = ""


def resolve_references(query: str, source: list[dict]) -> References:
    text = (
        unicodedata.normalize("NFKD", query.casefold())
        .encode("ascii", "ignore")
        .decode()
    )
    matches = []
    for index, item in enumerate(source):
        names = [item["title"]]
        if item.get("provider") == "local" and item.get("external_id"):
            names.append(item["external_id"])
        for name in names:
            tokens = normalize(name).split()
            if not tokens:
                continue
            pattern = r"\b" + r"[\W_]+".join(map(re.escape, tokens)) + r"\b"
            matches.extend(
                (m.start(), m.end(), index) for m in re.finditer(pattern, text)
            )
    result = References()
    mentions, spans = {}, []
    last_end, previous_negative = 0, False
    for start, end, index in sorted(matches, key=lambda row: (row[0], -row[1])):
        # Same title from different providers must be excluded in both catalogs.
        if spans and (start, end) == spans[-1]:
            mentions[index] = mentions.get(index, False) or previous_negative
            continue
        if start < last_end:
            continue
        bridge = text[last_end:start]
        bridge = re.split(r"[.!?;:\n]|\b(?:mas|porem|contudo)\b", bridge)[-1]
        words = normalize(bridge)
        negative = bool(
            re.search(
                r"\b(?:sem|exceto|evite|evitar|nao quero|nao gostei de)(?: \w+){0,2}$",
                words,
            )
            or (
                previous_negative
                and re.fullmatch(r"[\s,]*(?:(?:e|ou|nem)[\s,]*)*", text[last_end:start])
            )
        )
        mentions[index] = mentions.get(index, False) or negative
        spans.append((start, end))
        last_end, previous_negative = end, negative
    rejected = {
        normalize(source[index]["title"])
        for index, negative in mentions.items()
        if negative
    }
    for index in mentions:
        item = source[index]
        title = item["title"]
        result.blocked_ids.add(str(item["id"]))
        if normalize(title) in rejected:
            if title not in result.negative:
                result.negative.append(title)
        else:
            if title not in result.positive:
                result.positive.append(title)
            result.tags.update(item.get("tags", item.get("genres", [])))
    # Titles are entities, not mood/genre words (e.g. a title containing "dark").
    for start, end in reversed(spans):
        text = text[:start] + "obra" + text[end:]
    result.context = text
    return result
