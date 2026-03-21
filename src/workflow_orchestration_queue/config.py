"""Configuration management using Pydantic Settings."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Required settings
    github_token: SecretStr
    github_repo: str  # format: "owner/repo"
    sentinel_bot_login: str

    # Optional settings
    webhook_secret: SecretStr | None = None
    sentinel_heartbeat_interval: int = 300

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "",  # no prefix
    }


# Singleton instance
settings = Settings()
