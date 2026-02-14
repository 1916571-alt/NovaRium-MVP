from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.deps import get_current_user
from apps.api.schemas.auth import CurrentUser
from apps.api.schemas.community import (
    CommunityCommentCreateRequest,
    CommunityCommentItem,
    CommunityCommentListResponse,
    CommunityForkCreateRequest,
    CommunityForkResponse,
    CommunityPostCreateRequest,
    CommunityPostItem,
    CommunityPostListResponse,
)
from apps.api.services.community import (
    create_comment_for_user,
    create_post_for_user,
    fork_experiment_for_user,
    list_comments_for_user,
    list_posts_for_user,
)
from apps.api.services.users import ensure_app_user


router = APIRouter(prefix="/community")


@router.get("/posts", response_model=CommunityPostListResponse)
def list_posts(
    project_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    sort_by: str = Query(default="recent", pattern="^(recent|ranked)$"),
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    items = [
        CommunityPostItem(**x)
        for x in list_posts_for_user(current_user.user_id, project_id, limit, sort_by)
    ]
    return CommunityPostListResponse(items=items, count=len(items))


@router.post("/posts", response_model=CommunityPostItem, status_code=status.HTTP_201_CREATED)
def create_post(
    body: CommunityPostCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = create_post_for_user(current_user.user_id, body)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return CommunityPostItem(**row)


@router.get("/posts/{post_id}/comments", response_model=CommunityCommentListResponse)
def list_comments(
    post_id: str,
    limit: int = Query(default=100, ge=1, le=300),
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    items = [
        CommunityCommentItem(**x)
        for x in list_comments_for_user(current_user.user_id, post_id, limit)
    ]
    return CommunityCommentListResponse(items=items, count=len(items))


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommunityCommentItem,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    post_id: str,
    body: CommunityCommentCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = create_comment_for_user(current_user.user_id, post_id, body)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return CommunityCommentItem(**row)


@router.post("/forks", response_model=CommunityForkResponse, status_code=status.HTTP_201_CREATED)
def fork_experiment(
    body: CommunityForkCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    ensure_app_user(current_user.user_id, current_user.email)
    try:
        row = fork_experiment_for_user(current_user.user_id, body)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    return CommunityForkResponse(**row)
