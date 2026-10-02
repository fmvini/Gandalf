from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.database.session import get_session
from app.models import User
from app.routes.auth import current_user
from app.schemas.favorite import (
    FavoriteCreate,
    FavoriteList,
    FavoriteResponse,
    FavoriteStatus,
    FavoriteStatusRequest,
    FavoriteType,
)
from app.services.favorite_service import FavoriteService

router = APIRouter(prefix="/api/v1/users/me/favorites", tags=["favorites"])


def favorite_service(
    session: Annotated[Session, Depends(get_session)],
) -> FavoriteService:
    return FavoriteService(session)


@router.post("", response_model=FavoriteResponse, status_code=201)
async def create(
    request: Request,
    body: FavoriteCreate,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[FavoriteService, Depends(favorite_service)],
    response: Response,
):
    recommendation = await run_in_threadpool(
        request.app.state.recommendation_service.get_result, str(body.recommendation_id)
    )
    saved, created = await run_in_threadpool(
        service.create, user.id, body, recommendation
    )
    response.status_code = 201 if created else 200
    return saved


@router.get("", response_model=FavoriteList)
def list_favorites(
    user: Annotated[User, Depends(current_user)],
    service: Annotated[FavoriteService, Depends(favorite_service)],
    type: Annotated[FavoriteType | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
):
    return service.list_favorites(user.id, type, limit, offset)


@router.post("/status", response_model=FavoriteStatus)
def status(
    body: FavoriteStatusRequest,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[FavoriteService, Depends(favorite_service)],
):
    return service.status(user.id, body)


@router.delete("/{favorite_id}", status_code=204)
def delete(
    favorite_id: UUID,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[FavoriteService, Depends(favorite_service)],
) -> Response:
    service.delete(user.id, favorite_id)
    return Response(status_code=204)
