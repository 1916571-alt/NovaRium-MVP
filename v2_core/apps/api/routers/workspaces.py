from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.deps import get_current_user
from apps.api.schemas.auth import CurrentUser
from apps.api.schemas.workspaces import (
    WorkspaceCreateRequest,
    WorkspaceItem,
    WorkspaceListResponse,
    WorkspaceMemberAddRequest,
    WorkspaceRetentionAuditItem,
    WorkspaceRetentionAuditListResponse,
    WorkspaceRetentionUpdateRequest,
)
from apps.api.services.users import ensure_app_user
from apps.api.services.workspaces import (
    add_member_to_workspace_for_user,
    create_workspace_for_user,
    list_workspace_retention_audit_for_user,
    list_workspaces_for_user,
    update_workspace_retention_for_user,
)


router = APIRouter(prefix="/workspaces")


@router.get("", response_model=WorkspaceListResponse)
def list_workspaces(current_user: CurrentUser = Depends(get_current_user)):
    ensure_app_user(current_user.user_id, current_user.email)
    items = [WorkspaceItem(**x) for x in list_workspaces_for_user(current_user.user_id)]
    return WorkspaceListResponse(items=items, count=len(items))


@router.post("", response_model=WorkspaceItem, status_code=status.HTTP_201_CREATED)
def create_workspace(
    body: WorkspaceCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    item = create_workspace_for_user(current_user.user_id, body)
    return WorkspaceItem(**item)


@router.post("/{workspace_id}/members", status_code=status.HTTP_204_NO_CONTENT)
def add_member(
    workspace_id: str,
    body: WorkspaceMemberAddRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        add_member_to_workspace_for_user(current_user.user_id, workspace_id, body)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return None


@router.put("/{workspace_id}/retention", response_model=WorkspaceItem)
def update_workspace_retention(
    workspace_id: str,
    body: WorkspaceRetentionUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        item = update_workspace_retention_for_user(current_user.user_id, workspace_id, body)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return WorkspaceItem(**item)


@router.get("/{workspace_id}/retention-audit", response_model=WorkspaceRetentionAuditListResponse)
def list_workspace_retention_audit(
    workspace_id: str,
    changed_by_user_id: str | None = Query(default=None),
    changed_at_from: str | None = Query(default=None),
    changed_at_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    items = [
        WorkspaceRetentionAuditItem(**x)
        for x in list_workspace_retention_audit_for_user(
            current_user.user_id,
            workspace_id=workspace_id,
            changed_by_user_id=changed_by_user_id,
            changed_at_from=changed_at_from,
            changed_at_to=changed_at_to,
            limit=limit,
        )
    ]
    return WorkspaceRetentionAuditListResponse(items=items, count=len(items))
