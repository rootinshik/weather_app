"""Registry for all weather fetcher implementations.

This module imports all concrete fetcher classes and registers them
with the FetcherFactory. Must be imported before creating any fetchers.
"""

import logging

from app.fetchers.factory import FetcherFactory
from app.fetchers.openweathermap import OpenWeatherMapFetcher
from app.fetchers.weatherapi import WeatherAPIFetcher

logger = logging.getLogger(__name__)


def register_all_fetchers() -> None:
    """Register all available fetcher implementations with the factory.

    This function should be called once during application startup
    before any fetchers are created.
    """
    FetcherFactory.register_fetcher("rest", OpenWeatherMapFetcher)
    FetcherFactory.register_fetcher("weatherapi", WeatherAPIFetcher)

    logger.info(f"Registered {len(FetcherFactory.get_registered_types())} fetcher type(s)")


# Auto-register on module import
register_all_fetchers()
