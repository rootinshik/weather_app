"""Weather data fetchers package."""

from app.fetchers.base import AbstractWeatherFetcher
from app.fetchers.factory import FetcherFactory, load_fetchers_from_config_dir

# Import registry to auto-register all fetchers
from app.fetchers import registry  # noqa: F401

__all__ = [
    "AbstractWeatherFetcher",
    "FetcherFactory",
    "load_fetchers_from_config_dir",
]
