from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)


@dataclass
class Settings:
    """Runtime configuration surfaced through environment variables."""

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./smart_resume.db")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    max_shortlist: int = int(os.getenv("SHORTLIST_SIZE", "5"))
    enable_debug: bool = os.getenv("DEBUG", "false").lower() == "true"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance so FastAPI dependency injection is cheap."""

    return Settings()
