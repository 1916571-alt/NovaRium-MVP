from fastapi import APIRouter, Depends, Header, HTTPException, status

from apps.api.deps import get_current_user
from apps.api.schemas.auth import (
    AuthResponse,
    CurrentUser,
    RefreshTokenRequest,
    SignInRequest,
    SignOutResponse,
    SignUpRequest,
)
from apps.api.services.auth import refresh_token, sign_in, sign_out, sign_up
from apps.api.services.users import ensure_app_user


router = APIRouter(prefix="/auth")


@router.get("/me", response_model=CurrentUser)
def get_me(current_user: CurrentUser = Depends(get_current_user)):
    ensure_app_user(current_user.user_id, current_user.email)
    return current_user


@router.post("/sign-up", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def post_sign_up(body: SignUpRequest):
    try:
        data = sign_up(body.email, body.password)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    user = data.get("user") or {}
    return AuthResponse(
        access_token=data.get("access_token"),
        refresh_token=data.get("refresh_token"),
        token_type=data.get("token_type"),
        expires_in=data.get("expires_in"),
        user_id=user.get("id"),
        email=user.get("email"),
        raw=data,
    )


@router.post("/sign-in", response_model=AuthResponse)
def post_sign_in(body: SignInRequest):
    try:
        data = sign_in(body.email, body.password)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    user = data.get("user") or {}
    if user.get("id"):
        ensure_app_user(str(user["id"]), user.get("email"))

    return AuthResponse(
        access_token=data.get("access_token"),
        refresh_token=data.get("refresh_token"),
        token_type=data.get("token_type"),
        expires_in=data.get("expires_in"),
        user_id=user.get("id"),
        email=user.get("email"),
        raw=data,
    )


@router.post("/refresh", response_model=AuthResponse)
def post_refresh(body: RefreshTokenRequest):
    try:
        data = refresh_token(body.refresh_token)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    user = data.get("user") or {}
    if user.get("id"):
        ensure_app_user(str(user["id"]), user.get("email"))

    return AuthResponse(
        access_token=data.get("access_token"),
        refresh_token=data.get("refresh_token"),
        token_type=data.get("token_type"),
        expires_in=data.get("expires_in"),
        user_id=user.get("id"),
        email=user.get("email"),
        raw=data,
    )


@router.post("/sign-out", response_model=SignOutResponse)
def post_sign_out(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )
    access_token = authorization.split(" ", 1)[1].strip()

    try:
        sign_out(access_token)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return SignOutResponse(ok=True, message="Signed out")
