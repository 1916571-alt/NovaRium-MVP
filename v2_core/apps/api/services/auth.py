import json
from urllib import error, request

from apps.api.core.config import settings


def _ensure_auth_config() -> None:
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise RuntimeError("SUPABASE_URL or SUPABASE_ANON_KEY is missing")


def _post_json(url: str, payload: dict, extra_headers: dict | None = None) -> dict:
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "apikey": settings.supabase_anon_key,
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    req = request.Request(
        url=url,
        data=body,
        method="POST",
        headers=headers,
    )

    try:
        with request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="ignore")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"message": raw}
        raise ValueError(parsed) from exc


def sign_up(email: str, password: str) -> dict:
    _ensure_auth_config()
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/signup"
    return _post_json(url, {"email": email, "password": password})


def sign_in(email: str, password: str) -> dict:
    _ensure_auth_config()
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/token?grant_type=password"
    return _post_json(url, {"email": email, "password": password})


def refresh_token(refresh_token_value: str) -> dict:
    _ensure_auth_config()
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/token?grant_type=refresh_token"
    return _post_json(url, {"refresh_token": refresh_token_value})


def sign_out(access_token: str) -> dict:
    _ensure_auth_config()
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/logout"
    return _post_json(
        url,
        {},
        extra_headers={"Authorization": f"Bearer {access_token}"},
    )
