from dataclasses import dataclass


@dataclass
class Feature:
    name: str
    description: str
    unit: str
    min_value: float
    max_value: float


FEATURES: dict[str, Feature] = {
    "temperature": Feature(
        name="temperature",
        description="Температура воздуха",
        unit="°C",
        min_value=-50.0,
        max_value=50.0,
    ),
    "feels_like": Feature(
        name="feels_like",
        description="Ощущаемая температура с учётом ветра и влажности",
        unit="°C",
        min_value=-60.0,
        max_value=55.0,
    ),
    "wind_speed": Feature(
        name="wind_speed",
        description="Скорость ветра",
        unit="м/с",
        min_value=0.0,
        max_value=40.0,
    ),
    "humidity": Feature(
        name="humidity",
        description="Относительная влажность воздуха",
        unit="%",
        min_value=0.0,
        max_value=100.0,
    ),
    "pressure": Feature(
        name="pressure",
        description="Атмосферное давление",
        unit="гПа",
        min_value=950.0,
        max_value=1050.0,
    ),
    "precipitation_type": Feature(
        name="precipitation_type",
        description="Тип осадков: 0 — нет, 1 — дождь, 2 — снег, 3 — мокрый снег",
        unit="категория",
        min_value=0.0,
        max_value=3.0,
    ),
    "precipitation_amount": Feature(
        name="precipitation_amount",
        description="Количество осадков за час",
        unit="мм",
        min_value=0.0,
        max_value=50.0,
    ),
    "cloudiness": Feature(
        name="cloudiness",
        description="Облачность",
        unit="%",
        min_value=0.0,
        max_value=100.0,
    ),
}

FEATURE_NAMES: list[str] = list(FEATURES.keys())
