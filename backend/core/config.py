"""Core configuration using pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OmniRoute API
    omniroute_api_key: str = "your_api_key_here"
    omniroute_base_url: str = "https://api.omniroute.ai/v1"

    # Database
    database_url: str = "sqlite:///./olaisearch.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MLflow
    mlflow_tracking_uri: str = "file:./mlflow"

    # Application
    debug: bool = True
    log_level: str = "INFO"

    # Model IDs (will be loaded from config/models.yaml)
    vlm_model_id: str = "gpt-4-vision-preview"
    text_llm_model_id: str = "gpt-4-turbo-preview"
    embedder_model_id: str = "text-embedding-3-large"

    # Upload limits
    max_upload_size_mb: int = 50

    # Provider settings
    provider_timeout_seconds: int = 120
    provider_max_retries: int = 3


settings = Settings()
