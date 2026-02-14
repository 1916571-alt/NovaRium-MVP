from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.deps import get_current_user
from apps.api.schemas.auth import CurrentUser
from apps.api.schemas.sql_lab import (
    SqlChallengeCreateRequest,
    SqlChallengeItem,
    SqlChallengeListResponse,
    SqlExecuteRequest,
    SqlExecuteResponse,
    SqlSnippetCreateRequest,
    SqlSnippetItem,
    SqlSnippetListResponse,
    SqlSnippetUpdateRequest,
    SqlSubmissionCreateRequest,
    SqlSubmissionResponse,
)
from apps.api.services.sql_lab import (
    create_challenge_for_user,
    create_snippet_for_user,
    delete_snippet_for_user,
    execute_readonly_sql,
    list_challenges_for_user,
    list_snippets_for_user,
    submit_challenge_for_user,
    update_snippet_for_user,
)
from apps.api.services.users import ensure_app_user


router = APIRouter(prefix="/sql")


@router.post("/execute", response_model=SqlExecuteResponse)
def execute_sql(
    body: SqlExecuteRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        result = execute_readonly_sql(current_user.user_id, body.query, body.max_rows)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return SqlExecuteResponse(**result)


@router.get("/challenges", response_model=SqlChallengeListResponse)
def list_challenges(
    project_id: str | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    items = [
        SqlChallengeItem(**x)
        for x in list_challenges_for_user(current_user.user_id, project_id)
    ]
    return SqlChallengeListResponse(items=items, count=len(items))


@router.post(
    "/challenges",
    response_model=SqlChallengeItem,
    status_code=status.HTTP_201_CREATED,
)
def create_challenge(
    body: SqlChallengeCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = create_challenge_for_user(current_user.user_id, body)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return SqlChallengeItem(**row)


@router.post(
    "/challenges/{challenge_id}/submit",
    response_model=SqlSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_challenge(
    challenge_id: str,
    body: SqlSubmissionCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = submit_challenge_for_user(current_user.user_id, challenge_id, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return SqlSubmissionResponse(**row)


@router.get("/snippets", response_model=SqlSnippetListResponse)
def list_snippets(
    project_id: str | None = Query(default=None),
    q: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    pinned_only: bool = Query(default=False),
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    items = [
        SqlSnippetItem(**x)
        for x in list_snippets_for_user(
            current_user.user_id,
            project_id,
            q=q,
            tag=tag,
            pinned_only=pinned_only,
        )
    ]
    return SqlSnippetListResponse(items=items, count=len(items))


@router.post(
    "/snippets",
    response_model=SqlSnippetItem,
    status_code=status.HTTP_201_CREATED,
)
def create_snippet(
    body: SqlSnippetCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = create_snippet_for_user(current_user.user_id, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return SqlSnippetItem(**row)


@router.delete("/snippets/{snippet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snippet(
    snippet_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        delete_snippet_for_user(current_user.user_id, snippet_id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return None


@router.put("/snippets/{snippet_id}", response_model=SqlSnippetItem)
def update_snippet(
    snippet_id: str,
    body: SqlSnippetUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = update_snippet_for_user(current_user.user_id, snippet_id, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return SqlSnippetItem(**row)
