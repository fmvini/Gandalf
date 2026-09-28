from uuid import UUID

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import AppError
from app.schemas.recommendation import DiscoveryRequest, ReadingRequest

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.post("/music")
async def music(request: Request, body: DiscoveryRequest):
    return await request.app.state.recommendation_service.recommend("music", body)


@router.post("/books")
async def books(request: Request, body: DiscoveryRequest):
    if body.filters.model_dump(exclude_none=True):
        raise AppError(
            422,
            "VALIDATION_ERROR",
            "Filtros de voz e energia se aplicam apenas a músicas.",
        )
    return await request.app.state.recommendation_service.recommend("books", body)


@router.post("/read-with-music")
async def reading(request: Request, body: ReadingRequest):
    book = await run_in_threadpool(
        request.app.state.book_service.get_by_id, body.book_id
    )
    return await request.app.state.recommendation_service.soundtrack(book, body)


@router.get("/{recommendation_id}/items/{item_id}/explanation")
async def explanation(request: Request, recommendation_id: UUID, item_id: UUID):
    return request.app.state.recommendation_service.explanation(
        str(recommendation_id), str(item_id)
    )
