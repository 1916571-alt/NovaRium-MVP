from pydantic import BaseModel


class CurrentUser(BaseModel):
    user_id: str
    email: str | None = None
    role: str | None = None


class SignUpRequest(BaseModel):
    email: str
    password: str


class SignInRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
    user_id: str | None = None
    email: str | None = None
    raw: dict


class SignOutResponse(BaseModel):
    ok: bool
    message: str
