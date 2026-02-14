from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.deps import get_current_user
from apps.api.schemas.auth import CurrentUser
from apps.api.schemas.journeys import MyJourneyResponse
from apps.api.services.journeys import get_my_journey_for_project
from apps.api.services.users import ensure_app_user


router = APIRouter(prefix="/journeys")


@router.get("/me", response_model=MyJourneyResponse)
def get_my_journey(
    project_id: str = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    row = get_my_journey_for_project(current_user.user_id, project_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journey not found for this project",
        )
    return MyJourneyResponse(**row)

