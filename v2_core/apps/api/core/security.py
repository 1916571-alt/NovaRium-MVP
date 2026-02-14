from apps.api.core.config import settings


def decode_access_token(token: str) -> dict:
    try:
        from jose import JWTError, jwt
    except ModuleNotFoundError as exc:
        raise RuntimeError("python-jose is required for token verification") from exc

    if settings.supabase_jwt_secret:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    # Dev fallback: allow unsigned decode when JWT secret is not configured.
    # This keeps local demos usable, but should not be used in production.
    return jwt.get_unverified_claims(token)
