"""Configuration management for TortSignal."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


@dataclass
class DatabaseConfig:
    url: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ValueError("DATABASE_URL environment variable is required")
        return cls(url=url)


@dataclass
class OpenAIConfig:
    api_key: str
    model: str = "gpt-4o-mini"

    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return cls(api_key=api_key, model=model)


@dataclass
class UniCourtConfig:
    api_key: str
    base_url: str

    @classmethod
    def from_env(cls) -> "UniCourtConfig":
        api_key = os.getenv("UNICOURT_API_KEY")
        base_url = os.getenv("UNICOURT_BASE_URL")
        if not api_key or not base_url:
            raise ValueError("UNICOURT_API_KEY and UNICOURT_BASE_URL are required")
        return cls(api_key=api_key, base_url=base_url)


@dataclass
class OpenFDAConfig:
    api_key: str | None = None  # Optional - works without key at lower rate limits

    @classmethod
    def from_env(cls) -> "OpenFDAConfig":
        return cls(api_key=os.getenv("OPENFDA_API_KEY"))


@dataclass
class AppConfig:
    log_level: str = "INFO"
    discovery_days: int = 7
    discovery_limit: int = 100

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            discovery_days=int(os.getenv("DISCOVERY_DAYS", "7")),
            discovery_limit=int(os.getenv("DISCOVERY_LIMIT", "100")),
        )


@dataclass
class Config:
    """Main configuration container."""

    database: DatabaseConfig
    openai: OpenAIConfig
    unicourt: UniCourtConfig
    openfda: OpenFDAConfig
    app: AppConfig

    @classmethod
    def from_env(cls) -> "Config":
        """Load all configuration from environment variables."""
        return cls(
            database=DatabaseConfig.from_env(),
            openai=OpenAIConfig.from_env(),
            unicourt=UniCourtConfig.from_env(),
            openfda=OpenFDAConfig.from_env(),
            app=AppConfig.from_env(),
        )


def get_config() -> Config:
    """Get the application configuration."""
    return Config.from_env()
