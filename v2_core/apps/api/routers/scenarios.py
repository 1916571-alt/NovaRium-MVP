from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.deps import get_current_user
from apps.api.schemas.auth import CurrentUser
from apps.api.schemas.scenarios import (
    ScenarioExportResponse,
    ScenarioImportRequest,
    ScenarioImportResponse,
    ScenarioImportValidateResponse,
    ScenarioShareCreateRequest,
    ScenarioShareCreateResponse,
    ScenarioShareRevokeResponse,
)
from apps.api.services.scenarios import (
    create_scenario_share_for_user,
    export_scenario_pack_for_user,
    import_scenario_pack_for_user,
    revoke_scenario_share_for_user,
    resolve_scenario_share,
    validate_scenario_pack_payload,
)
from apps.api.services.users import ensure_app_user


router = APIRouter(prefix="/scenarios")


@router.get("/export", response_model=ScenarioExportResponse)
def export_scenario_pack(
    project_id: str = Query(..., min_length=1),
    schema_version: str | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = export_scenario_pack_for_user(
            current_user.user_id,
            project_id,
            schema_version=schema_version,
        )
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
    return ScenarioExportResponse(**row)


@router.post(
    "/import",
    response_model=ScenarioImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_scenario_pack(
    body: ScenarioImportRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = import_scenario_pack_for_user(
            current_user.user_id,
            workspace_id=body.workspace_id,
            project_name=body.project_name,
            schema_version=body.schema_version,
            payload=body.payload,
        )
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
    return ScenarioImportResponse(**row)


@router.post("/import/validate", response_model=ScenarioImportValidateResponse)
def validate_scenario_pack(
    body: ScenarioImportRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = validate_scenario_pack_payload(body.schema_version, body.payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return ScenarioImportValidateResponse(**row)


@router.post("/shares", response_model=ScenarioShareCreateResponse, status_code=status.HTTP_201_CREATED)
def create_scenario_share(
    body: ScenarioShareCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = create_scenario_share_for_user(
            user_id=current_user.user_id,
            project_id=body.project_id,
            schema_version=body.schema_version,
            expires_hours=body.expires_hours,
        )
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
    return ScenarioShareCreateResponse(**row)


@router.get("/shares/{share_token}", response_model=ScenarioExportResponse)
def resolve_share_link(share_token: str):
    try:
        row = resolve_scenario_share(share_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return ScenarioExportResponse(**row)


@router.delete("/shares/{share_token}", response_model=ScenarioShareRevokeResponse)
def revoke_share_link(
    share_token: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = revoke_scenario_share_for_user(current_user.user_id, share_token)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return ScenarioShareRevokeResponse(**row)
