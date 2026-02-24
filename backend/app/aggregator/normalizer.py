"""Unit conversion utilities for weather data normalization.

All weather data is stored in SI units:
- Temperature: Celsius (°C)
- Wind speed: meters per second (m/s)
- Pressure: hectopascals (hPa)
- Visibility: meters (m)
"""


def kph_to_ms(kph: float) -> float:
    """Convert kilometers per hour to meters per second.

    Args:
        kph: Speed in km/h

    Returns:
        Speed in m/s
    """
    return kph / 3.6


def mph_to_ms(mph: float) -> float:
    """Convert miles per hour to meters per second.

    Args:
        mph: Speed in mph

    Returns:
        Speed in m/s
    """
    return mph * 0.44704


def fahrenheit_to_celsius(f: float) -> float:
    """Convert Fahrenheit to Celsius.

    Args:
        f: Temperature in Fahrenheit

    Returns:
        Temperature in Celsius
    """
    return (f - 32) * 5 / 9


def kelvin_to_celsius(k: float) -> float:
    """Convert Kelvin to Celsius.

    Args:
        k: Temperature in Kelvin

    Returns:
        Temperature in Celsius
    """
    return k - 273.15


def mmhg_to_hpa(mmhg: float) -> float:
    """Convert millimeters of mercury to hectopascals.

    Args:
        mmhg: Pressure in mmHg

    Returns:
        Pressure in hPa
    """
    return mmhg * 1.33322


def inhg_to_hpa(inhg: float) -> float:
    """Convert inches of mercury to hectopascals.

    Args:
        inhg: Pressure in inHg

    Returns:
        Pressure in hPa
    """
    return inhg * 33.8639


def km_to_m(km: float) -> float:
    """Convert kilometers to meters.

    Args:
        km: Distance in kilometers

    Returns:
        Distance in meters
    """
    return km * 1000


def miles_to_m(miles: float) -> float:
    """Convert miles to meters.

    Args:
        miles: Distance in miles

    Returns:
        Distance in meters
    """
    return miles * 1609.34


# Mapping of unit names to conversion functions
UNIT_CONVERTERS: dict[str, dict[str, callable]] = {
    "temperature": {
        "f": fahrenheit_to_celsius,
        "fahrenheit": fahrenheit_to_celsius,
        "k": kelvin_to_celsius,
        "kelvin": kelvin_to_celsius,
        "c": lambda x: x,  # Already in Celsius
        "celsius": lambda x: x,
    },
    "wind_speed": {
        "kph": kph_to_ms,
        "km/h": kph_to_ms,
        "kmh": kph_to_ms,
        "mph": mph_to_ms,
        "miles/h": mph_to_ms,
        "m/s": lambda x: x,  # Already in m/s
        "ms": lambda x: x,
    },
    "pressure": {
        "mmhg": mmhg_to_hpa,
        "mm": mmhg_to_hpa,
        "inhg": inhg_to_hpa,
        "in": inhg_to_hpa,
        "hpa": lambda x: x,  # Already in hPa
        "mb": lambda x: x,  # Millibars = hPa
        "mbar": lambda x: x,
    },
    "visibility": {
        "km": km_to_m,
        "kilometers": km_to_m,
        "mi": miles_to_m,
        "miles": miles_to_m,
        "m": lambda x: x,  # Already in meters
        "meters": lambda x: x,
    },
}


def normalize_value(field: str, value: float, from_unit: str) -> float:
    """Normalize a value to SI units based on field type and source unit.

    Args:
        field: Field name (e.g., "temperature", "wind_speed", "pressure")
        value: Value to convert
        from_unit: Source unit (e.g., "kph", "f", "mmhg")

    Returns:
        Converted value in SI units

    Raises:
        ValueError: If field type or unit is not supported
    """
    field_lower = field.lower()
    from_unit_lower = from_unit.lower()

    if field_lower not in UNIT_CONVERTERS:
        raise ValueError(f"Unsupported field type for normalization: {field}")

    converters = UNIT_CONVERTERS[field_lower]

    if from_unit_lower not in converters:
        raise ValueError(
            f"Unsupported unit '{from_unit}' for field '{field}'. "
            f"Supported units: {list(converters.keys())}"
        )

    converter = converters[from_unit_lower]
    return converter(value)


def apply_conversions(
    data: dict[str, float], conversions: dict[str, dict[str, str]]
) -> dict[str, float]:
    """Apply unit conversions to weather data dictionary.

    Args:
        data: Dictionary with weather data
        conversions: Conversion specifications from config
                    Format: {"field_name": {"from": "kph", "to": "m/s"}}

    Returns:
        Dictionary with converted values

    Example:
        data = {"wind_speed": 36.0}
        conversions = {"wind_speed": {"from": "kph", "to": "m/s"}}
        result = apply_conversions(data, conversions)
        # result = {"wind_speed": 10.0}
    """
    result = data.copy()

    for field, conversion_spec in conversions.items():
        if field not in result:
            continue

        value = result[field]
        if value is None:
            continue

        from_unit = conversion_spec.get("from", "").lower()
        to_unit = conversion_spec.get("to", "").lower()

        # Use custom factor if provided, otherwise use standard conversion
        if "factor" in conversion_spec:
            result[field] = value * conversion_spec["factor"]
        else:
            # Determine field type for normalization
            field_type = _infer_field_type(field)
            result[field] = normalize_value(field_type, value, from_unit)

    return result


def _infer_field_type(field_name: str) -> str:
    """Infer the type of measurement from field name.

    Args:
        field_name: Name of the field (e.g., "wind_speed", "temperature")

    Returns:
        Field type for normalization lookup

    Raises:
        ValueError: If field type cannot be inferred
    """
    field_lower = field_name.lower()

    if "temp" in field_lower or "feels" in field_lower:
        return "temperature"
    if "wind" in field_lower and "speed" in field_lower:
        return "wind_speed"
    if "pressure" in field_lower:
        return "pressure"
    if "visibility" in field_lower or "vis" in field_lower:
        return "visibility"

    raise ValueError(f"Cannot infer field type from field name: {field_name}")
