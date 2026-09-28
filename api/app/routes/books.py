from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Request

from app.schemas.book import BookItem, BookSearchResponse

router = APIRouter(prefix="/api/v1/books", tags=["books"])


@router.get("/search", response_model=BookSearchResponse)
async def search_books(
    request: Request,
    q: Annotated[str, Query(min_length=2, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    provider: Literal["local", "open_library"] | None = None,
) -> BookSearchResponse:
    if provider and provider != request.app.state.book_service.provider.name:
        from app.core.exceptions import AppError

        raise AppError(
            422, "VALIDATION_ERROR", "Esse provider não está ativo nesta instalação."
        )
    return await request.app.state.book_service.search(q, limit)


@router.get("/{book_id}", response_model=BookItem)
def get_book(request: Request, book_id: UUID) -> BookItem:
    return request.app.state.book_service.get_by_id(book_id)
