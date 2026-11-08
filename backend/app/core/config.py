"""Settings come from environment variables (and the repo-root .env file for local work)."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> parents[3] is the repo root
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    app_name: str = "Series Tracker"
    environment: str = "local"  # "local" or "production"
    # SQLite file (created in the folder you start uvicorn from). For PostgreSQL in Week 2:
    # postgresql+psycopg://tracker:<password>@127.0.0.1:5432/tracker
    database_url: str = "sqlite:///./tracker.db"
    llm_api_key: str | None = None  # server-side only, never sent to the frontend
    # Hosts this app answers to (defeats DNS rebinding). Add your real name when you deploy (Week 15).
    allowed_hosts: str = "localhost,127.0.0.1,[::1]"

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")


settings = Settings()
