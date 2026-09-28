from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request

from app.schemas.book import BookSearchResponse

router = APIRouter(prefix="/api/v1/books", tags=["books"])


@router.get("/search", response_model=BookSearchResponse)
async def search_books(
    request: Request,
    q: Annotated[str, Query(min_length=2, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    provider: Literal["open_library"] | None = None,
) -> BookSearchResponse:
    # O parâmetro é parte do contrato; existe apenas um provider nesta etapa.
    _ = provider
    return await request.app.state.book_service.search(q, limit)
