"""Clothing recommendation service using a pre-trained scikit-learn pipeline.

The model is loaded once at application startup via load_model() classmethod
(singleton pattern). If the model files are absent, is_available() returns False
and callers should return HTTP 503.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.recommendation import ClothingRecommendationResponse
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Clothing categories — inlined from ml/model/labels.py because the backend
# container does not have the ml package on its Python path.
# ---------------------------------------------------------------------------


@dataclass
class _ClothingCategory:
    name: str
    description: str
    items: list[str]


_CLOTHING_CATEGORIES: dict[str, _ClothingCategory] = {
    "light_summer": _ClothingCategory(
        name="light_summer",
        description="Очень жарко — лёгкая летняя одежда",
        items=["футболка", "шорты", "сандалии", "солнечные очки", "кепка"],
    ),
    "moderate_warm": _ClothingCategory(
        name="moderate_warm",
        description="Тепло — повседневная одежда без верхней",
        items=["лёгкая рубашка", "джинсы или брюки", "кроссовки"],
    ),
    "light_jacket": _ClothingCategory(
        name="light_jacket",
        description="Прохладно — лёгкая верхняя одежда",
        items=["ветровка или лёгкая куртка", "джинсы", "кроссовки"],
    ),
    "warm_dry": _ClothingCategory(
        name="warm_dry",
        description="Холодно и сухо — тёплая одежда",
        items=["тёплая куртка", "свитер", "джинсы", "закрытая обувь"],
    ),
    "warm_rain": _ClothingCategory(
        name="warm_rain",
        description="Холодно и дождливо — непромокаемая одежда",
        items=["непромокаемая куртка", "свитер", "джинсы", "резиновые сапоги", "зонт"],
    ),
    "winter_light": _ClothingCategory(
        name="winter_light",
        description="Лёгкий мороз — зимняя одежда",
        items=[
            "зимняя куртка",
            "тёплый свитер",
            "тёплые брюки",
            "зимние ботинки",
            "шапка",
            "перчатки",
        ],
    ),
    "winter_heavy": _ClothingCategory(
        name="winter_heavy",
        description="Сильный мороз — тёплая зимняя одежда",
        items=[
            "пуховик",
            "тёплый свитер",
            "термобельё",
            "зимние брюки",
            "зимние ботинки",
            "шапка",
            "шарф",
            "тёплые перчатки",
        ],
    ),
    "winter_extreme": _ClothingCategory(
        name="winter_extreme",
        description="Экстремальный мороз — максимальное утепление",
        items=[
            "тёплый пуховик",
            "термобельё",
            "флисовый свитер",
            "зимние брюки на утеплителе",
            "валенки или тёплые зимние ботинки",
            "меховая шапка",
            "тёплый шарф",
            "варежки",
        ],
    ),
}

# Mapping from backend string values to integer codes the model was trained on.
# generate_dataset.py: 0=none, 1=rain, 2=snow, 3=mixed/sleet
_PRECIP_TYPE_MAP: dict[str | None, int] = {
    None: 0,
    "none": 0,
    "rain": 1,
    "snow": 2,
    "sleet": 3,
    "mixed": 3,
}

# Feature order must match ml/model/features.py FEATURE_NAMES exactly:
# temperature, feels_like, wind_speed, humidity, pressure,
# precipitation_type, precipitation_amount, cloudiness
_N_FEATURES = 8


class RecommendationService:
    """Service for ML-based clothing recommendations.

    Class-level attributes hold the loaded pipeline and label encoder so that
    the model is shared across all instances created per request.
    """

    _pipeline: Any = None
    _label_encoder: Any = None
    _model_loaded: bool = False

    @classmethod
    def load_model(cls) -> None:
        """Load model artifacts from paths configured in settings.yaml.

        Called once during application startup. If ML is disabled or model
        files are absent, logs a warning and leaves _model_loaded as False.
        """
        enabled: bool = settings.app_config.get("ml", "enabled", default=True)
        if not enabled:
            logger.info("ML recommendations disabled via settings (ml.enabled=false)")
            return

        model_path = Path(
            settings.app_config.get("ml", "model_path", default="")
        )
        encoder_path = Path(
            settings.app_config.get("ml", "label_encoder_path", default="")
        )

        if not model_path.exists() or not encoder_path.exists():
            logger.warning(
                "ML model artifacts not found — recommendations unavailable. "
                "Run: docker compose --profile training run ml-train"
            )
            return

        try:
            cls._pipeline = joblib.load(model_path)
            cls._label_encoder = joblib.load(encoder_path)
            cls._model_loaded = True
            logger.info("ML model loaded from %s", model_path)
        except Exception as exc:
            logger.error("Failed to load ML model: %s", exc)
            cls._model_loaded = False

    @classmethod
    def is_available(cls) -> bool:
        """Return True if the model was successfully loaded."""
        return cls._model_loaded

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_recommendation(
        self, city_id: int
    ) -> ClothingRecommendationResponse | None:
        """Predict clothing category for a city's current aggregated weather.

        Args:
            city_id: Database city ID.

        Returns:
            ClothingRecommendationResponse on success, None if no weather data
            is available for the city.

        Raises:
            RuntimeError: If the model is not loaded or prediction fails.
        """
        if not self.is_available():
            raise RuntimeError("ML model is not available")

        weather_service = WeatherService(self.db)
        weather = await weather_service.get_aggregated_current(city_id)

        if weather is None:
            return None

        features = self._extract_features(weather)
        feature_array = np.array([features], dtype=float)

        predicted_index: int = self._pipeline.predict(feature_array)[0]
        category_name: str = self._label_encoder.inverse_transform([predicted_index])[0]

        category = _CLOTHING_CATEGORIES.get(category_name)
        if category is None:
            logger.error("Unknown predicted category: %r", category_name)
            raise RuntimeError(f"Unknown ML category: {category_name!r}")

        return ClothingRecommendationResponse(
            city_id=city_id,
            category=category.name,
            description=category.description,
            items=list(category.items),
        )

    @staticmethod
    def _extract_features(weather: Any) -> list[float]:
        """Convert AggregatedWeather to an ordered feature vector.

        None values are replaced with safe defaults so the model always
        receives a complete, valid input vector.
        """
        precip_int = _PRECIP_TYPE_MAP.get(weather.precipitation_type, 0)
        return [
            weather.temperature if weather.temperature is not None else 0.0,
            weather.feels_like if weather.feels_like is not None else 0.0,
            weather.wind_speed if weather.wind_speed is not None else 0.0,
            float(weather.humidity) if weather.humidity is not None else 50.0,
            weather.pressure if weather.pressure is not None else 1013.0,
            float(precip_int),
            (
                weather.precipitation_amount
                if weather.precipitation_amount is not None
                else 0.0
            ),
            float(weather.cloudiness) if weather.cloudiness is not None else 0.0,
        ]
