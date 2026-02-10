import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings


_ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")

_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def _substitute_env_vars(value: Any) -> Any:
    """Recursively substitute ${ENV_VAR} placeholders with environment variable values."""
    if isinstance(value, str):
        def _replace(match: re.Match) -> str:
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                raise ValueError(
                    f"Required environment variable '{var_name}' is not set. "
                    f"Please set it in .env or environment before starting the application."
                )
            return env_value

        return _ENV_VAR_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _substitute_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env_vars(item) for item in value]
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and substitute environment variables."""
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return _substitute_env_vars(raw)


def _load_settings_yaml() -> dict[str, Any]:
    settings_path = _CONFIG_DIR / "settings.yaml"
    if not settings_path.exists():
        return {}
    return _load_yaml(settings_path)


class AppConfig:
    """Parsed content of settings.yaml."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def get(self, *keys: str, default: Any = None) -> Any:
        node: Any = self._data
        for key in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(key, default)
        return node


class Settings(BaseSettings):
    # Database — read from env directly (used by database.py / alembic)
    db_user: str = "weather"
    db_password: str = "weather_secret"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "weather_db"

    # Auth
    admin_api_key: str = "changeme"

    # External API keys
    owm_api_key: str = ""
    weatherapi_key: str = ""

    # Telegram
    telegram_bot_token: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("admin_api_key")
    @classmethod
    def _admin_key_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("ADMIN_API_KEY must not be empty")
        return v

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def app_config(self) -> AppConfig:
        if not hasattr(self, "_app_config"):
            object.__setattr__(self, "_app_config", AppConfig(_load_settings_yaml()))
        return self._app_config  # type: ignore[attr-defined]


settings = Settings()
