"""Application settings from environment variables."""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # ============================================================================
    # REQUIRED: API Keys (must be in .env)
    # ============================================================================
    gemini_api_key: str
    perplexity_api_key: str
    mapbox_access_token: str

    # ============================================================================
    # OPTIONAL: Agent Configuration
    # ============================================================================
    agent_name: str = "mapbox_location_agent"
    agent_debug: bool = False

    # ============================================================================
    # OPTIONAL: Langfuse Observability (for monitoring)
    # ============================================================================
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_base_url: str = "https://cloud.langfuse.com"

    # ============================================================================
    # OPTIONAL: BrightData (not currently used)
    # ============================================================================
    brightdata_token: Optional[str] = None

    # ============================================================================
    # OPTIONAL: Redis Configuration
    # ============================================================================
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_password: Optional[str] = None

    # ============================================================================
    # OPTIONAL: FastAPI Server Configuration
    # ============================================================================
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # ============================================================================
    # OPTIONAL: Session Management
    # ============================================================================
    session_ttl_hours: int = 24
    max_sessions: int = 100
    max_messages_per_session: int = 50

    # ============================================================================
    # OPTIONAL: Model Configuration
    # ============================================================================
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_temperature: float = 0.7
    gemini_max_tokens: int = 2048

    # ============================================================================
    # OPTIONAL: Logging
    # ============================================================================
    log_level: str = "INFO"


# Global settings instance
settings = Settings()
