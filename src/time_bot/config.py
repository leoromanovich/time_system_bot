"""Application configuration and settings management."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Project-level settings loaded from environment variables/.env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: SecretStr = Field(..., alias="TELEGRAM_BOT_TOKEN")
    openai_api_key: SecretStr = Field(..., alias="OPENAI_API_KEY")
    openai_base_url: str = Field("https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    model_name: str = Field(..., alias="MODEL_NAME")
    sgr_endpoint: Optional[str] = Field(None, alias="SGR_ENDPOINT")

    obsidian_vault_dir: Path = Field(..., alias="OBSIDIAN_VAULT_DIR")
    timezone: str = Field("Europe/Riga", alias="TIMEZONE")

    cache_dir: Path = Field(Path("cache"), alias="CACHE_DIR")
    log_dir: Path = Field(Path("logs"), alias="LOG_DIR")

    food_track_model_name: Optional[str] = Field(None, alias="FOOD_TRACK_MODEL_NAME")
    food_track_model_endpoint: Optional[str] = Field(None, alias="FOOD_TRACK_MODEL_ENDPOINT")
    food_track_openai_api_key: Optional[SecretStr] = Field(
        None, alias="FOOD_TRACK_OPENAI_API_KEY"
    )
    food_track_obsidian_vault_dir: Optional[Path] = Field(
        None, alias="FOOD_TRACK_OBSIDIAN_VAULT_DIR"
    )
    food_track_photo_intake_url: Optional[str] = Field(
        None, alias="FOOD_TRACK_PHOTO_INTAKE_URL"
    )
    food_track_photo_intake_token: Optional[str] = Field(
        None, alias="FOOD_TRACK_PHOTO_INTAKE_TOKEN"
    )


_SETTINGS: Optional[Settings] = None


def get_settings() -> Settings:
    """Return cached settings instance."""

    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = Settings()
    return _SETTINGS


__all__ = ["Settings", "get_settings"]
