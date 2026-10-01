from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.database.session import get_session
from app.models import User
from app.routes.auth import current_user
from app.schemas.playlist import PlaylistCreate, PlaylistDetail, PlaylistList
from app.services.playlist_service import PlaylistService

router = APIRouter(prefix="/api/v1/playlists", tags=["playlists"])


def playlist_service(
    session: Annotated[Session, Depends(get_session)],
) -> PlaylistService:
    return PlaylistService(session)


@router.post("", response_model=PlaylistDetail, status_code=201)
async def create(
    request: Request,
    body: PlaylistCreate,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[PlaylistService, Depends(playlist_service)],
    response: Response,
):
    # Read the ephemeral cache on the event loop, before database work runs in
    # a worker thread. The snapshot cannot change during save.
    recommendation = (
        request.app.state.recommendation_service.get_result(
            str(body.source_recommendation_id)
        )
        if body.source_recommendation_id is not None
        else None
    )
    result = await run_in_threadpool(service.create, user.id, body, recommendation)
    response.headers["Location"] = f"/api/v1/playlists/{result.id}"
    return result


@router.get("", response_model=PlaylistList)
def list_playlists(
    user: Annotated[User, Depends(current_user)],
    service: Annotated[PlaylistService, Depends(playlist_service)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
):
    return service.list_playlists(user.id, limit, offset)


@router.get("/{playlist_id}", response_model=PlaylistDetail)
def detail(
    playlist_id: UUID,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[PlaylistService, Depends(playlist_service)],
):
    return service.get(user.id, playlist_id)


@router.delete("/{playlist_id}", status_code=204)
def delete(
    playlist_id: UUID,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[PlaylistService, Depends(playlist_service)],
) -> Response:
    service.delete(user.id, playlist_id)
    return Response(status_code=204)
