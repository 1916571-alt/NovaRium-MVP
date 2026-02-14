from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "NovaRium V2 API"
    app_env: str = "dev"
    app_debug: bool = True
    api_prefix: str = "/v2"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""
    scenario_share_secret: str = ""
    database_url: str = ""
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    admin_bypass_enabled: bool = False
    admin_bypass_user_id: str = "00000000-0000-0000-0000-000000000001"
    admin_bypass_email: str = "admin@local.dev"
    admin_bypass_role: str = "owner"


settings = Settings()
