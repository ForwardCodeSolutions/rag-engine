"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration via .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # Embedding model
    embedding_model: str = "intfloat/multilingual-e5-large"

    # API
    api_key: str = "changeme"

    # Logging
    log_level: str = "info"

    # App
    app_version: str = "0.1.0"
