import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.config import _load_yaml

logger = logging.getLogger(__name__)

_SOURCES_DIR = Path(__file__).parent.parent.parent / "config" / "sources"


@dataclass
class UnitConversion:
    from_unit: str
    to_unit: str
    factor: float


@dataclass
class Endpoint:
    path: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceConfig:
    name: str
    source_type: str  # "rest" | "parser"
    priority: int
    enabled: bool
    base_url: str
    timeout: int
    api_key: str
    headers: dict[str, str]
    endpoints: dict[str, Endpoint]
    field_mapping: dict[str, str]
    css_selectors: dict[str, str]
    unit_conversions: dict[str, UnitConversion]


def _parse_source(data: dict[str, Any]) -> SourceConfig:
    connection: dict[str, Any] = data.get("connection", {})

    endpoints: dict[str, Endpoint] = {}
    for ep_name, ep_data in data.get("endpoints", {}).items():
        endpoints[ep_name] = Endpoint(
            path=ep_data.get("path", ""),
            params=ep_data.get("params", {}),
        )

    unit_conversions: dict[str, UnitConversion] = {}
    for field_name, conv_data in data.get("unit_conversions", {}).items():
        unit_conversions[field_name] = UnitConversion(
            from_unit=conv_data.get("from", ""),
            to_unit=conv_data.get("to", ""),
            factor=float(conv_data.get("factor", 1.0)),
        )

    return SourceConfig(
        name=data.get("name", ""),
        source_type=data.get("type", "rest"),
        priority=int(data.get("priority", 99)),
        enabled=bool(data.get("enabled", True)),
        base_url=connection.get("base_url", ""),
        timeout=int(connection.get("timeout", 10)),
        api_key=connection.get("api_key", ""),
        headers=connection.get("headers", {}),
        endpoints=endpoints,
        field_mapping=data.get("field_mapping", {}),
        css_selectors=data.get("css_selectors", {}),
        unit_conversions=unit_conversions,
    )


class SourceManager:
    def __init__(self, sources_dir: Path = _SOURCES_DIR) -> None:
        self._sources_dir = sources_dir
        self._sources: dict[str, SourceConfig] = {}
        self._loaded = False

    def load(self) -> None:
        """Load all YAML source configs from the sources directory."""
        if not self._sources_dir.exists():
            logger.warning("Sources config directory not found: %s", self._sources_dir)
            return

        yaml_files = list(self._sources_dir.glob("*.yaml"))
        if not yaml_files:
            logger.warning("No source YAML files found in %s", self._sources_dir)

        for yaml_path in sorted(yaml_files):
            try:
                data = _load_yaml(yaml_path)
                config = _parse_source(data)
                self._sources[config.name] = config
                logger.info(
                    "Loaded source config: %s (priority=%d, enabled=%s)",
                    config.name,
                    config.priority,
                    config.enabled,
                )
            except ValueError as exc:
                logger.error("Failed to load source config %s: %s", yaml_path.name, exc)
                raise
            except Exception as exc:
                logger.error("Unexpected error loading %s: %s", yaml_path.name, exc)
                raise

        self._loaded = True

    def get_all(self) -> list[SourceConfig]:
        """Return all enabled source configs sorted by priority."""
        return sorted(
            (s for s in self._sources.values() if s.enabled),
            key=lambda s: s.priority,
        )

    def get(self, name: str) -> SourceConfig | None:
        return self._sources.get(name)

    @property
    def is_loaded(self) -> bool:
        return self._loaded


source_manager = SourceManager()
