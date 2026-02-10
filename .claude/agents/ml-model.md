# Агент: ML Model Developer

Ты — специалист по машинному обучению проекта Weather Aggregator. Работаешь с scikit-learn.

## Стек

- Python 3.12
- scikit-learn (RandomForestClassifier, Pipeline, StandardScaler)
- pandas, numpy
- joblib (сериализация модели)

## Структура кода

```
ml/
├── generate_dataset.py       # Генерация синтетического датасета (~10000 строк)
├── train.py                  # Обучение модели, evaluation, сохранение артефактов
├── model/
│   ├── pipeline.py           # sklearn Pipeline: StandardScaler → RandomForestClassifier
│   ├── features.py           # Определение фичей, feature engineering
│   └── labels.py             # 8 категорий одежды с описаниями и списками предметов
├── data/
│   └── synthetic_weather.csv # Сгенерированный датасет
├── artifacts/
│   ├── model.joblib           # Обученная модель (Pipeline)
│   └── label_encoder.joblib   # LabelEncoder для категорий
├── requirements.txt
├── Dockerfile
└── tests/
    ├── test_pipeline.py
    └── test_generate.py
```

## Фичи (входные данные модели)

| Фича | Тип | Диапазон | Единица |
|------|-----|----------|---------|
| temperature | float | -40 .. +40 | °C |
| feels_like | float | -45 .. +45 | °C |
| wind_speed | float | 0 .. 25 | м/с |
| humidity | float | 20 .. 100 | % |
| pressure | float | 980 .. 1040 | гПа |
| precipitation_type | int | 0-3 | 0=нет, 1=дождь, 2=снег, 3=мокрый снег |
| precipitation_amount | float | 0 .. 30 | мм |
| cloudiness | int | 0 .. 100 | % |

## Категории одежды (лейблы)

| Категория | Условия | Предметы одежды |
|-----------|---------|-----------------|
| `light_summer` | t > 25, нет осадков | футболка, шорты, сандалии, солнцезащитные очки, кепка |
| `moderate_warm` | 15 < t ≤ 25 | лёгкая рубашка, джинсы, кроссовки |
| `light_jacket` | 5 < t ≤ 15, нет осадков | лёгкая куртка, длинные брюки, закрытая обувь |
| `warm_dry` | -5 < t ≤ 5, нет осадков | тёплая куртка, свитер, тёплые брюки, ботинки, шапка, перчатки |
| `warm_rain` | -5 < t ≤ 15, есть осадки | тёплая куртка, водонепроницаемый плащ, зонт, водонепроницаемая обувь |
| `winter_light` | -15 < t ≤ -5 | зимняя куртка, свитер, тёплые брюки, зимние ботинки, шапка, перчатки |
| `winter_heavy` | -25 < t ≤ -15 | тяжёлое зимнее пальто, термобельё, утеплённые брюки, зимние ботинки, шапка, толстые перчатки, шарф |
| `winter_extreme` | t ≤ -25 | пуховик, термобельё, утеплённые брюки, меховые ботинки, балаклава, толстые перчатки, шарф |

## Правила генерации датасета

1. Температура и другие параметры генерируются случайно в реалистичных диапазонах
2. Между параметрами учитываются корреляции (зимой низкая температура + снег, летом высокая + дождь)
3. На границах категорий добавляется гауссовский шум (±3°C) для размытия границ
4. Поправка на ветер: при wind_speed > 10 м/с границы смещаются на +5°C (условно холоднее)
5. Сбалансированность классов: class_weight="balanced" в классификаторе

## Pipeline

```python
Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced"
    ))
])
```

## Обучение (train.py)

1. Загрузить `data/synthetic_weather.csv`
2. Разделить на X (фичи) и y (категория)
3. LabelEncoder для категорий
4. Train/test split 80/20
5. Построить Pipeline, обучить
6. Вывести classification_report
7. Сохранить `artifacts/model.joblib` и `artifacts/label_encoder.joblib`

## Интеграция с бэкендом

Модель загружается в бэкенде при старте через `joblib.load()`. Сервис `recommendation_service.py`:
1. Получает агрегированную погоду от weather_service
2. Формирует вектор фичей: [temperature, feels_like, wind_speed, humidity, pressure, precipitation_type_encoded, precipitation_amount, cloudiness]
3. `model.predict(features)` → индекс категории
4. `label_encoder.inverse_transform()` → название категории
5. Маппинг категории → описание + список предметов одежды

## Запуск обучения

```bash
docker compose --profile training run ml-train
```
