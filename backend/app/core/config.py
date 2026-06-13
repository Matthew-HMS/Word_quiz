from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


_REPO_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILES = (
    str(_REPO_ROOT / ".env"),
    str(_REPO_ROOT / "backend" / ".env"),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILES, env_file_encoding="utf-8", extra="ignore")

    # DB
    # Default to SQLite for zero-setup local dev.
    # For multi-user production, set DATABASE_URL to Postgres (recommended).
    database_url: str = "sqlite:///./wordquiz.db"

    # Auth
    jwt_secret_key: str = "CHANGE_ME_DEV_ONLY"
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60 * 24

    # Google SSO (the only auth method). Set to your OAuth 2.0 Web client ID.
    google_client_id: str = ""

    # CORS
    cors_allow_origins: str = "http://localhost:5173"

    # Data
    repo_root: Path = _REPO_ROOT


settings = Settings()
