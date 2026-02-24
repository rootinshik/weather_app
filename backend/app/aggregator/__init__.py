"""Weather data aggregation and normalization package."""

from app.aggregator.normalizer import (
    UNIT_CONVERTERS,
    apply_conversions,
    fahrenheit_to_celsius,
    inhg_to_hpa,
    kelvin_to_celsius,
    km_to_m,
    kph_to_ms,
    miles_to_m,
    mmhg_to_hpa,
    mph_to_ms,
    normalize_value,
)

__all__ = [
    "normalize_value",
    "apply_conversions",
    "kph_to_ms",
    "mph_to_ms",
    "fahrenheit_to_celsius",
    "kelvin_to_celsius",
    "mmhg_to_hpa",
    "inhg_to_hpa",
    "km_to_m",
    "miles_to_m",
    "UNIT_CONVERTERS",
]
