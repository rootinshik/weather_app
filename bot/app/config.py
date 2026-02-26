"""Bot configuration: loads bot_settings.yaml with env var substitution."""

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).parent.parent / "config"
_ENV_VAR_RE = re.compile(r"\$\{([^}]+)\}")


def _substitute_env_vars(value: Any) -> Any:
    """Recursively replace ${VAR} placeholders with environment variable values."""
    if isinstance(value, str):
        def _replace(m: re.Match) -> str:
            return os.environ.get(m.group(1), "")
        return _ENV_VAR_RE.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _substitute_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env_vars(item) for item in value]
    return value


def _load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return _substitute_env_vars(raw)


@dataclass
class BotSettings:
    token: str
    backend_base_url: str
    backend_timeout: int
    log_level: str

    @classmethod
    def from_yaml(cls, path: Path | None = None) -> "BotSettings":
        cfg_path = path or (_CONFIG_DIR / "bot_settings.yaml")
        data = _load_yaml(cfg_path)

        return cls(
            token=data.get("bot", {}).get("token", ""),
            backend_base_url=data.get("backend", {}).get("base_url", "http://localhost:8000"),
            backend_timeout=data.get("backend", {}).get("timeout", 10),
            log_level=data.get("logging", {}).get("level", "INFO"),
        )


settings = BotSettings.from_yaml()
