from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.deps import get_current_user
from apps.api.schemas.analytics import (
    FunnelOverviewResponse,
    SimulationBootstrapRequest,
    SimulationBootstrapResponse,
    SimulationTemplateItem,
    SimulationTemplateListResponse,
)
from apps.api.schemas.auth import CurrentUser
from apps.api.services.analytics import (
    bootstrap_simulation_for_project,
    get_funnel_overview_for_user,
    list_simulation_templates,
)
from apps.api.services.users import ensure_app_user


router = APIRouter(prefix="/analytics")


@router.get("/templates", response_model=SimulationTemplateListResponse)
def get_templates(
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    items = [SimulationTemplateItem(**x) for x in list_simulation_templates()]
    return SimulationTemplateListResponse(items=items, count=len(items))


@router.post(
    "/projects/{project_id}/bootstrap",
    response_model=SimulationBootstrapResponse,
    status_code=status.HTTP_201_CREATED,
)
def bootstrap_simulation(
    project_id: str,
    body: SimulationBootstrapRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = bootstrap_simulation_for_project(current_user.user_id, project_id, body)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return SimulationBootstrapResponse(**row)


@router.get("/projects/{project_id}/funnel", response_model=FunnelOverviewResponse)
def get_funnel_overview(
    project_id: str,
    run_id: str | None = Query(default=None),
    experiment_id: str | None = Query(default=None),
    template: str | None = Query(default=None, pattern="^(commerce|content|saas)$"),
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    row = get_funnel_overview_for_user(
        current_user.user_id,
        project_id=project_id,
        run_id=run_id,
        experiment_id=experiment_id,
        template=template,
    )
    return FunnelOverviewResponse(**row)
