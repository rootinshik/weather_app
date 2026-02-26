"""Micro-tests for bot config loading."""

import os
from pathlib import Path

import pytest

from app.config import BotSettings


def _write_yaml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "bot_settings.yaml"
    p.write_text(content)
    return p


class TestBotSettings:
    def test_loads_defaults_without_env_vars(self, tmp_path):
        yaml_path = _write_yaml(tmp_path, """\
bot:
  token: ""
backend:
  base_url: "http://localhost:8000"
  timeout: 10
logging:
  level: "INFO"
""")
        cfg = BotSettings.from_yaml(yaml_path)
        assert cfg.token == ""
        assert cfg.backend_base_url == "http://localhost:8000"
        assert cfg.backend_timeout == 10
        assert cfg.log_level == "INFO"

    def test_substitutes_env_var_for_token(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot123:test")
        yaml_path = _write_yaml(tmp_path, """\
bot:
  token: "${TELEGRAM_BOT_TOKEN}"
backend:
  base_url: "http://backend:8000"
  timeout: 5
""")
        cfg = BotSettings.from_yaml(yaml_path)
        assert cfg.token == "bot123:test"

    def test_missing_env_var_becomes_empty_string(self, tmp_path, monkeypatch):
        monkeypatch.delenv("SOME_MISSING_VAR", raising=False)
        yaml_path = _write_yaml(tmp_path, """\
bot:
  token: "${SOME_MISSING_VAR}"
""")
        cfg = BotSettings.from_yaml(yaml_path)
        assert cfg.token == ""
