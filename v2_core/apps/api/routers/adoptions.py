from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.deps import get_current_user
from apps.api.schemas.adoptions import AdoptionCreateRequest, AdoptionItem, AdoptionRolloutRequest
from apps.api.schemas.auth import CurrentUser
from apps.api.services.adoptions import (
    create_adoption_for_user,
    rollback_adoption_for_user,
    update_adoption_rollout_for_user,
)
from apps.api.services.users import ensure_app_user


router = APIRouter(prefix="/adoptions")


@router.post("", response_model=AdoptionItem, status_code=status.HTTP_201_CREATED)
def create_adoption(
    body: AdoptionCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = create_adoption_for_user(current_user.user_id, body)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return AdoptionItem(**row)


@router.post("/{adoption_id}/rollout", response_model=AdoptionItem)
def update_rollout(
    adoption_id: int,
    body: AdoptionRolloutRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = update_adoption_rollout_for_user(
            current_user.user_id, adoption_id, body.traffic_percentage
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return AdoptionItem(**row)


@router.post("/{adoption_id}/rollback", response_model=AdoptionItem)
def rollback_adoption(
    adoption_id: int,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = rollback_adoption_for_user(current_user.user_id, adoption_id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return AdoptionItem(**row)

