"""Application configuration, loaded from environment / .env.

Paths are anchored to the backend directory rather than the process working
directory. Without that, ``uvicorn --app-dir backend`` run from the repository
root would load no ``.env`` at all and quietly create a second, empty SQLite
file next to wherever it happened to be started.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "hello-world"
    tagline: str = "Learn what the industry actually wants."

    database_url: str = "sqlite:///./helloworld.db"
    cors_origins: str = (
        "http://localhost:5190,http://127.0.0.1:5190,http://localhost:5173"
    )

    enabled_connectors: str = "mock_dataset"

    seed_postings_per_role: int = 180
    seed_random_state: int = 20260811
    seed_history_months: int = 12

    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-5"
    llm_extraction_enabled: bool = False

    confidence_high_min_postings: int = 150
    confidence_medium_min_postings: int = 40

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def connector_list(self) -> list[str]:
        return [c.strip() for c in self.enabled_connectors.split(",") if c.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def resolved_database_url(self) -> str:
        """``database_url`` with any relative SQLite path made absolute.

        Keeps ``manage.py seed`` (run from ``backend/``) and the API server
        (often run from the repository root) pointing at the same file.
        """
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            return self.database_url

        raw = self.database_url[len(prefix) :]
        if raw.startswith(":memory:") or raw.startswith("/"):
            return self.database_url

        path = Path(raw)
        if path.is_absolute():
            return self.database_url
        return f"{prefix}{(BACKEND_DIR / path).resolve().as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
