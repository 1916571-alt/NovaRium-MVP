from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.deps import get_current_user
from apps.api.schemas.auth import CurrentUser
from apps.api.schemas.events import EventIngestBatchRequest, EventIngestBatchResponse
from apps.api.services.events import ingest_events_for_user
from apps.api.services.users import ensure_app_user


router = APIRouter(prefix="/events")


@router.post(
    "/ingest",
    response_model=EventIngestBatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_events(
    body: EventIngestBatchRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = ingest_events_for_user(current_user.user_id, body)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return EventIngestBatchResponse(**row)
