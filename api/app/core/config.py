from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Gandalf"
    app_version: str = "0.1.0"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    open_library_base_url: str = "https://openlibrary.org"
    open_library_contact_email: str = ""
    book_search_cache_ttl_seconds: int = Field(default=300, ge=0, le=3600)
    database_url: str | None = None
    jwt_secret: str = ""
    access_token_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_days: int = Field(default=7, ge=1, le=30)
    auth_rate_limit_per_minute: int = Field(default=10, ge=1, le=100)
