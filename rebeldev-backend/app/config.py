"""
Application configuration for OG-Ollama-UI
Loads from .env or environment variables
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Environment-aware application settings"""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # or "production"
    LOG_LEVEL: str = "INFO"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "*"]

    # Auth (optional)
    REQUIRE_AUTH: bool = False
    AUTH_TOKEN: Optional[str] = None

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # Perplexity
    PERPLEXITY_API_KEY: Optional[str] = None

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: int = 300  # seconds

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global config instance
settings = AppConfig()
