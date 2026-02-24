"""Factory for creating weather fetcher instances from YAML configuration."""

import logging
from pathlib import Path
from typing import Any

import yaml

from app.core.config import _substitute_env_vars
from app.fetchers.base import AbstractWeatherFetcher

logger = logging.getLogger(__name__)


class FetcherFactory:
    """Factory for creating weather fetcher instances.

    Loads YAML configuration files and creates appropriate fetcher instances
    based on the source type (rest API, HTML parser, etc.).
    """

    # Registry of fetcher classes by type
    # Will be populated when concrete implementations are created
    _fetcher_registry: dict[str, type[AbstractWeatherFetcher]] = {}

    @classmethod
    def register_fetcher(cls, source_type: str, fetcher_class: type[AbstractWeatherFetcher]) -> None:
        """Register a fetcher class for a specific source type.

        Args:
            source_type: Type identifier (e.g., "rest", "parser")
            fetcher_class: Concrete fetcher class to register

        Example:
            FetcherFactory.register_fetcher("rest", RestApiFetcher)
            FetcherFactory.register_fetcher("parser", HtmlParserFetcher)
        """
        cls._fetcher_registry[source_type.lower()] = fetcher_class
        logger.info(f"Registered fetcher class for type '{source_type}': {fetcher_class.__name__}")

    @classmethod
    def create_from_config(cls, config: dict[str, Any]) -> AbstractWeatherFetcher:
        """Create a fetcher instance from configuration dictionary.

        Args:
            config: Configuration dictionary (typically loaded from YAML)
                   Must contain a "type" field (e.g., "rest", "parser")

        Returns:
            Instance of appropriate fetcher class

        Raises:
            ValueError: If source type is not registered or missing from config
            KeyError: If required configuration fields are missing
        """
        if "type" not in config:
            raise ValueError("Configuration must contain a 'type' field")

        source_type = config["type"].lower()

        if source_type not in cls._fetcher_registry:
            available_types = list(cls._fetcher_registry.keys())
            raise ValueError(
                f"No fetcher registered for type '{source_type}'. "
                f"Available types: {available_types}. "
                f"Did you forget to call FetcherFactory.register_fetcher()?"
            )

        fetcher_class = cls._fetcher_registry[source_type]
        logger.debug(f"Creating fetcher of type '{source_type}': {fetcher_class.__name__}")

        return fetcher_class(config)

    @classmethod
    def create_from_yaml_file(cls, yaml_path: Path) -> AbstractWeatherFetcher:
        """Create a fetcher instance from a YAML configuration file.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            Instance of appropriate fetcher class

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValueError: If YAML is invalid or source type not registered
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        logger.info(f"Loading fetcher configuration from: {yaml_path}")

        # Load and parse YAML
        with open(yaml_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config:
            raise ValueError(f"Empty or invalid YAML file: {yaml_path}")

        # Substitute environment variables (${VAR_NAME} → value from .env)
        config = _substitute_env_vars(config)

        # Add source file path to config for debugging
        config["_config_file"] = str(yaml_path)

        return cls.create_from_config(config)

    @classmethod
    def create_all_from_directory(cls, sources_dir: Path) -> list[AbstractWeatherFetcher]:
        """Create fetcher instances for all YAML files in a directory.

        Args:
            sources_dir: Path to directory containing YAML config files

        Returns:
            List of fetcher instances (only enabled sources)

        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        if not sources_dir.exists():
            raise FileNotFoundError(f"Sources directory not found: {sources_dir}")

        if not sources_dir.is_dir():
            raise ValueError(f"Path is not a directory: {sources_dir}")

        logger.info(f"Loading fetchers from directory: {sources_dir}")

        fetchers: list[AbstractWeatherFetcher] = []
        yaml_files = list(sources_dir.glob("*.yaml")) + list(sources_dir.glob("*.yml"))

        if not yaml_files:
            logger.warning(f"No YAML files found in {sources_dir}")
            return fetchers

        for yaml_file in yaml_files:
            try:
                fetcher = cls.create_from_yaml_file(yaml_file)

                # Only include enabled fetchers
                if fetcher.is_enabled():
                    fetchers.append(fetcher)
                    logger.info(
                        f"Loaded fetcher '{fetcher.get_name()}' "
                        f"(type: {fetcher.get_type()}, priority: {fetcher.get_priority()})"
                    )
                else:
                    logger.info(f"Skipping disabled fetcher: {fetcher.get_name()}")

            except Exception as e:
                logger.error(f"Failed to load fetcher from {yaml_file}: {e}")
                # Continue loading other fetchers even if one fails
                continue

        logger.info(f"Successfully loaded {len(fetchers)} enabled fetcher(s)")
        return fetchers

    @classmethod
    def get_registered_types(cls) -> list[str]:
        """Get list of registered fetcher types.

        Returns:
            List of type identifiers
        """
        return list(cls._fetcher_registry.keys())


def load_fetchers_from_config_dir() -> list[AbstractWeatherFetcher]:
    """Convenience function to load all fetchers from standard config directory.

    Returns:
        List of enabled fetcher instances

    Raises:
        FileNotFoundError: If config directory doesn't exist
    """
    # Get config directory (backend/config/sources/)
    config_dir = Path(__file__).parent.parent.parent / "config" / "sources"

    return FetcherFactory.create_all_from_directory(config_dir)
