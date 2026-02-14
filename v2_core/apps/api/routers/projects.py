from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.deps import get_current_user
from apps.api.schemas.auth import CurrentUser
from apps.api.schemas.projects import (
    ProjectCreateRequest,
    ProjectItem,
    ProjectListResponse,
)
from apps.api.services.projects import create_project_for_user, list_projects_for_user
from apps.api.services.users import ensure_app_user


router = APIRouter(prefix="/projects")


@router.get("", response_model=ProjectListResponse)
def list_projects(current_user: CurrentUser = Depends(get_current_user)):
    ensure_app_user(current_user.user_id, current_user.email)
    items = [ProjectItem(**x) for x in list_projects_for_user(current_user.user_id)]
    return ProjectListResponse(items=items, count=len(items))


@router.post("", response_model=ProjectItem, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        result = create_project_for_user(current_user.user_id, body)
        return ProjectItem(**result)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
