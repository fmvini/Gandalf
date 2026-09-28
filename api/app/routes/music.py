from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import AppError
from app.providers.local_catalog import MUSIC, normalize

router = APIRouter(prefix="/api/v1/music", tags=["music"])


@router.get("/search")
async def search(
    request: Request,
    q: Annotated[str, Query(min_length=2, max_length=180)],
    limit: Annotated[int, Query(ge=1, le=25)] = 20,
):
    if not q.strip():
        raise AppError(422, "VALIDATION_ERROR", "Informe título ou artista.")
    provider = getattr(request.app.state, "music_provider", None)
    if provider:
        return await provider.search(q, limit)
    items = [
        item
        for item in MUSIC
        if normalize(q) in normalize(item["title"] + " " + item["artist"])
    ]
    return {"items": items[:limit], "total": len(items), "provider": "local"}


@router.get("/{item_id}")
async def detail(request: Request, item_id: UUID):
    local = next((item for item in MUSIC if item["id"] == str(item_id)), None)
    if local:
        return local
    item = await run_in_threadpool(request.app.state.online_store.music_by_id, item_id)
    if item is None:
        raise AppError(404, "NOT_FOUND", "Música não encontrada no catálogo.")
    return item
