from fastapi import Depends, Header, HTTPException, status

from apps.api.core.config import settings
from apps.api.core.security import decode_access_token
from apps.api.schemas.auth import CurrentUser


def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        if settings.admin_bypass_enabled:
            return CurrentUser(
                user_id=settings.admin_bypass_user_id,
                email=settings.admin_bypass_email,
                role=settings.admin_bypass_role,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc

    user_id = str(payload.get("sub", ""))
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )

    return CurrentUser(
        user_id=user_id,
        email=payload.get("email"),
        role=payload.get("role"),
    )


CurrentUserDep = Depends(get_current_user)
