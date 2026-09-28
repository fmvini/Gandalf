import asyncio
import re
from time import monotonic
from uuid import NAMESPACE_URL, uuid5

import httpx

from app.core.exceptions import UpstreamError, UpstreamRateLimited, UpstreamTimeout
from app.schemas.book import BookItem, BookSearchResponse

WORK_KEY = re.compile(r"(?:/works/)?(OL\d+W)")
SEARCH_FIELDS = "key,title,author_name,first_publish_year,cover_i,subject,description"
MAX_DESCRIPTION_LENGTH = 2000
MAX_SUBJECTS = 12
MAX_SUBJECT_LENGTH = 120


def normalize_description(raw: object) -> str | None:
    if isinstance(raw, dict):
        raw = raw.get("value")
    if not isinstance(raw, str):
        return None
    description = raw.strip()
    return description[:MAX_DESCRIPTION_LENGTH] or None


def normalize_subjects(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    subjects: list[str] = []
    seen: set[str] = set()
    for value in raw:
        if not isinstance(value, str):
            continue
        subject = value.strip()[:MAX_SUBJECT_LENGTH].strip()
        key = subject.casefold()
        if subject and key not in seen:
            subjects.append(subject)
            seen.add(key)
        if len(subjects) == MAX_SUBJECTS:
            break
    return subjects


def normalize_book(raw: object) -> BookItem | None:
    if not isinstance(raw, dict):
        return None
    key = raw.get("key")
    title = raw.get("title")
    if not isinstance(key, str) or not isinstance(title, str) or not title.strip():
        return None
    match = WORK_KEY.fullmatch(key)
    if not match:
        return None
    external_id = match.group(1)
    authors = raw.get("author_name")
    cover_id = raw.get("cover_i")
    year = raw.get("first_publish_year")
    url = f"https://openlibrary.org/works/{external_id}"
    return BookItem(
        id=uuid5(NAMESPACE_URL, url),
        title=title.strip(),
        authors=[name for name in authors if isinstance(name, str) and name.strip()]
        if isinstance(authors, list)
        else [],
        publication_year=year
        if isinstance(year, int) and not isinstance(year, bool) and year > 0
        else None,
        description=normalize_description(raw.get("description")),
        subjects=normalize_subjects(raw.get("subject")),
        cover_url=f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
        if isinstance(cover_id, int) and not isinstance(cover_id, bool) and cover_id > 0
        else None,
        external_url=url,
        external_id=external_id,
    )


class OpenLibraryProvider:
    name = "open_library"

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str = "https://openlibrary.org",
        contact_email: str = "",
        request_interval_seconds: float = 1.0,
    ) -> None:
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.contact_email = contact_email.strip()
        self.request_interval_seconds = request_interval_seconds
        self._lock = asyncio.Lock()
        self._last_request_at = 0.0

    async def search(self, title: str, limit: int) -> BookSearchResponse:
        return await self._search({"title": title}, limit)

    async def discover(self, subject: str, limit: int) -> BookSearchResponse:
        return await self._search({"subject": subject[:180]}, limit)

    async def _search(self, query: dict, limit: int) -> BookSearchResponse:
        user_agent = "Gandalf/0.2.0 (https://github.com/fmvini/Gandalf)"
        if self.contact_email:
            user_agent += f" ({self.contact_email})"
        async with self._lock:
            elapsed = monotonic() - self._last_request_at
            if elapsed < self.request_interval_seconds:
                await asyncio.sleep(self.request_interval_seconds - elapsed)
            self._last_request_at = monotonic()
            try:
                response = await self.client.get(
                    f"{self.base_url}/search.json",
                    params={**query, "limit": limit, "fields": SEARCH_FIELDS},
                    headers={"User-Agent": user_agent},
                )
            except httpx.TimeoutException as exc:
                raise UpstreamTimeout() from exc
            except httpx.RequestError as exc:
                raise UpstreamError() from exc

        if response.status_code == 429:
            raise UpstreamRateLimited()
        if response.is_error:
            raise UpstreamError()
        try:
            payload = response.json()
        except ValueError as exc:
            raise UpstreamError() from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("docs"), list):
            raise UpstreamError()

        items = [
            book for raw in payload["docs"] if (book := normalize_book(raw)) is not None
        ]
        total = payload.get("numFound", payload.get("num_found", len(items)))
        if not isinstance(total, int) or isinstance(total, bool) or total < 0:
            total = len(items)
        return BookSearchResponse(items=items, total=total)
