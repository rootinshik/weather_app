"""
Генерация синтетического датасета для обучения модели рекомендаций по одежде.

Правила назначения лейблов (до поправки на ветер):
  light_summer   : effective_t >= 25
  moderate_warm  : 15 <= effective_t < 25, без осадков / лёгкие
  light_jacket   :  8 <= effective_t < 15, без снега
  warm_dry       :  0 <= effective_t <  8, без осадков
  warm_rain      :  0 <= effective_t <  8, дождь / мокрый снег
  winter_light   : -15 <= effective_t < 0
  winter_heavy   : -25 <= effective_t < -15
  winter_extreme : effective_t < -25

Поправка на ветер: wind_speed > 10 → effective_t = temperature - 5
Гауссовский шум (σ=3°C) на границах категорий для реалистичности.
Физические корреляции: зима → снег, лето → дождь (нет снега при t > +5).
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from ml.model.features import FEATURE_NAMES
from ml.model.labels import LABEL_NAMES

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

RANDOM_SEED = 42
N_SAMPLES = 10_000
OUTPUT_PATH = Path(__file__).parent / "data" / "synthetic_weather.csv"

# Доля шума (строки, где temperature получает случайный шум на границе)
BOUNDARY_NOISE_FRACTION = 0.15
BOUNDARY_NOISE_STD = 3.0  # σ для гауссовского шума на границах


def _assign_precip(
    temperature: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Генерация физически реалистичных осадков."""
    n = len(temperature)
    precip_type = np.zeros(n, dtype=float)   # 0 — нет осадков
    precip_amount = np.zeros(n, dtype=float)

    # Маски по сезонным зонам температуры
    is_winter = temperature < 0.0
    is_mixed = (temperature >= 0.0) & (temperature < 5.0)
    is_warm = temperature >= 5.0

    # Вероятности: зима — снег, переходная зона — мокрый снег, лето — дождь
    rain_prob_warm = 0.25
    snow_prob_winter = 0.30
    mixed_prob = 0.20

    # Тёплый дождь
    rain_mask = is_warm & (rng.random(n) < rain_prob_warm)
    precip_type[rain_mask] = 1  # дождь
    precip_amount[rain_mask] = rng.exponential(2.0, rain_mask.sum())

    # Снег зимой
    snow_mask = is_winter & (rng.random(n) < snow_prob_winter)
    precip_type[snow_mask] = 2  # снег
    precip_amount[snow_mask] = rng.exponential(1.5, snow_mask.sum())

    # Мокрый снег в переходной зоне
    mixed_mask = is_mixed & (rng.random(n) < mixed_prob)
    precip_type[mixed_mask] = 3  # мокрый снег
    precip_amount[mixed_mask] = rng.exponential(1.0, mixed_mask.sum())

    return precip_type, precip_amount


def _assign_label(effective_t: np.ndarray, precip_type: np.ndarray) -> np.ndarray:
    """Назначение лейблов по эффективной температуре и осадкам."""
    labels = np.empty(len(effective_t), dtype=object)

    has_rain = (precip_type == 1) | (precip_type == 3)  # дождь или мокрый снег

    labels[effective_t >= 25] = "light_summer"

    mask = (effective_t >= 15) & (effective_t < 25)
    labels[mask] = "moderate_warm"

    mask = (effective_t >= 8) & (effective_t < 15)
    labels[mask] = "light_jacket"

    mask = (effective_t >= 0) & (effective_t < 8) & ~has_rain
    labels[mask] = "warm_dry"

    mask = (effective_t >= 0) & (effective_t < 8) & has_rain
    labels[mask] = "warm_rain"

    mask = (effective_t >= -15) & (effective_t < 0)
    labels[mask] = "winter_light"

    mask = (effective_t >= -25) & (effective_t < -15)
    labels[mask] = "winter_heavy"

    labels[effective_t < -25] = "winter_extreme"

    return labels


def generate_dataset(n_samples: int = N_SAMPLES, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # --- temperature: равномерное распределение по диапазону [-40, 40] ---
    temperature = rng.uniform(-40.0, 40.0, n_samples)

    # --- Гауссовский шум на границах категорий ---
    boundaries = [-25.0, -15.0, 0.0, 8.0, 15.0, 25.0]
    noise_indices = rng.choice(
        n_samples,
        size=int(n_samples * BOUNDARY_NOISE_FRACTION),
        replace=False,
    )
    for idx in noise_indices:
        boundary = rng.choice(boundaries)
        temperature[idx] = boundary + rng.normal(0, BOUNDARY_NOISE_STD)

    temperature = np.clip(temperature, -50.0, 50.0)

    # --- wind_speed: логнормальное [0, 40] ---
    wind_speed = np.clip(rng.lognormal(mean=1.5, sigma=0.8, size=n_samples), 0.0, 40.0)

    # --- Поправка на ветер: effective_t = t - 5 при v > 10 м/с ---
    effective_t = temperature.copy()
    windy = wind_speed > 10.0
    effective_t[windy] -= 5.0

    # --- Физически реалистичные осадки ---
    precip_type, precip_amount = _assign_precip(temperature, rng)

    # --- Feels like: temperature - wind_chill + humidity correction ---
    humidity = rng.uniform(20.0, 100.0, n_samples)
    wind_chill = np.where(wind_speed > 5.0, 0.4 * (wind_speed - 5.0), 0.0)
    feels_like = np.clip(temperature - wind_chill, -60.0, 55.0)

    # --- Давление: нормальное ~1013 гПа ---
    pressure = np.clip(rng.normal(1013.0, 15.0, n_samples), 950.0, 1050.0)

    # --- Облачность ---
    # Коррелируем с осадками: при осадках облачность высокая
    cloudiness = np.where(
        precip_type > 0,
        rng.uniform(60.0, 100.0, n_samples),
        rng.uniform(0.0, 100.0, n_samples),
    )

    # --- Лейблы ---
    labels = _assign_label(effective_t, precip_type)

    df = pd.DataFrame(
        {
            "temperature": np.round(temperature, 1),
            "feels_like": np.round(feels_like, 1),
            "wind_speed": np.round(wind_speed, 1),
            "humidity": np.round(humidity, 1),
            "pressure": np.round(pressure, 1),
            "precipitation_type": precip_type.astype(int),
            "precipitation_amount": np.round(precip_amount, 2),
            "cloudiness": np.round(cloudiness, 1),
            "label": labels,
        }
    )

    # Убеждаемся, что порядок столбцов соответствует FEATURE_NAMES
    assert list(df.columns[:-1]) == FEATURE_NAMES, "Порядок колонок не совпадает с FEATURE_NAMES"
    assert set(df["label"].unique()) == set(LABEL_NAMES), (
        f"Не все лейблы присутствуют: {set(df['label'].unique())}"
    )

    return df


def main() -> None:
    logger.info("Генерация датасета (%d строк)...", N_SAMPLES)
    df = generate_dataset()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    logger.info("Датасет сохранён: %s", OUTPUT_PATH)
    logger.info("Форма: %s", df.shape)
    logger.info("Распределение лейблов:\n%s", df["label"].value_counts().to_string())


if __name__ == "__main__":
    main()
