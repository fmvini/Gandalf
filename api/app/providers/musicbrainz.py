import asyncio
import re
from time import monotonic
from urllib.parse import quote
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import AppError


def literal(text: str) -> str:
    return '"' + re.sub(r'([+\-!(){}\[\]^"~*?:\\/|&])', r"\\\1", text[:180]) + '"'


def normalize_recording(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get("title"), str):
        return None
    try:
        mbid = str(UUID(raw["id"]))
    except (KeyError, ValueError, TypeError, AttributeError):
        return None
    credits = raw.get("artist-credit")
    if not isinstance(credits, list):
        return None
    artist = "".join(
        credit["name"] + (credit.get("joinphrase") or "")
        for credit in credits
        if isinstance(credit, dict)
        and isinstance(credit.get("name"), str)
        and isinstance(credit.get("joinphrase", ""), (str, type(None)))
    ).strip()
    if not artist or not raw["title"].strip():
        return None
    raw_tags = raw.get("tags")
    tags = [
        tag["name"][:100]
        for tag in (raw_tags if isinstance(raw_tags, list) else [])
        if isinstance(tag, dict) and isinstance(tag.get("name"), str)
    ][:12]
    length = raw.get("length")
    duration = length if type(length) is int and 0 < length < 86_400_000 else None
    title = raw["title"].strip()[:300]
    url = f"https://musicbrainz.org/recording/{mbid}"
    return {
        "id": str(uuid5(NAMESPACE_URL, url)),
        "title": title,
        "artist": artist[:300],
        "tags": tags,
        "duration_ms": duration,
        "has_vocals": None,
        "energy": None,
        "provider": "musicbrainz",
        "external_id": mbid,
        "links": {
            "provider": url,
            "search": "https://www.youtube.com/results?search_query="
            + quote(title + " " + artist),
        },
    }


class MusicBrainzProvider:
    def __init__(self, client, store, ttl=3600, interval=1.1):
        self.client, self.store, self.ttl = client, store, ttl
        self.interval = interval
        self.lock = asyncio.Lock()
        self.last_call = 0.0

    async def search(self, query, limit=20, *, by_tag=False, offset=0):
        key = ("tag:" if by_tag else "text:") + query.strip().casefold()
        if offset:
            key = f"offset:{offset}:" + key
        async with self.lock:
            cached = await run_in_threadpool(self.store.get, "musicbrainz", key, limit)
            if cached is not None:
                return cached
            elapsed = monotonic() - self.last_call
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
            self.last_call = monotonic()
            search = ("tag:" if by_tag else "") + literal(query) + " AND video:false"
            try:
                response = await self.client.get(
                    "https://musicbrainz.org/ws/2/recording",
                    params={
                        "query": search,
                        "limit": limit,
                        "fmt": "json",
                        **({"offset": offset} if offset else {}),
                    },
                    headers={
                        "User-Agent": "Gandalf/0.2.0 (https://github.com/fmvini/Gandalf)"
                    },
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or not isinstance(
                    payload.get("recordings"), list
                ):
                    raise TypeError("Invalid MusicBrainz response")
            except (httpx.HTTPError, ValueError, TypeError) as exc:
                raise AppError(
                    503,
                    "MUSIC_PROVIDER_UNAVAILABLE",
                    "MusicBrainz indisponível. Tente novamente em instantes.",
                ) from exc
            items = [
                item
                for raw in payload["recordings"]
                if (item := normalize_recording(raw))
            ]
            items = list({item["id"]: item for item in items}.values())
            count = payload.get("count")
            has_more = (
                count > offset + limit
                if type(count) is int
                else len(payload["recordings"]) >= limit
            )
            result = {
                "items": items,
                "total": len(items),
                "provider": "musicbrainz",
                "has_more": has_more,
            }
            await run_in_threadpool(self.store.save_music, items)
            await run_in_threadpool(
                self.store.put, "musicbrainz", key, limit, result, self.ttl
            )
            return result
