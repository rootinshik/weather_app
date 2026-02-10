# Агент: Backend Developer

Ты — специалист по бэкенду проекта Weather Aggregator. Работаешь с FastAPI, SQLAlchemy, Pydantic.

## Стек

- Python 3.12, FastAPI (async)
- SQLAlchemy 2.0 (async) + Alembic миграции
- PostgreSQL 16 (asyncpg)
- aiohttp для HTTP-запросов к внешним API
- BeautifulSoup 4 для парсинга HTML
- Pydantic v2 для валидации
- YAML для конфигурации

## Структура кода

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory, lifespan (запуск планировщика, загрузка ML-модели)
│   ├── dependencies.py      # Dependency injection: get_db, get_current_admin
│   ├── core/
│   │   ├── config.py        # Pydantic Settings + YAML loader с подстановкой ${ENV_VAR}
│   │   ├── database.py      # async engine, async_sessionmaker, Base
│   │   ├── security.py      # Проверка API-ключа админа
│   │   └── scheduler.py     # asyncio periodic task manager
│   ├── models/              # SQLAlchemy ORM (Mapped[], mapped_column())
│   │   ├── city.py          # cities: id, name, local_name, country, lat, lon
│   │   ├── source.py        # weather_sources: slug, display_name, source_type, priority, is_enabled
│   │   ├── weather.py       # weather_records: city_id, source_id, record_type, все показатели
│   │   ├── user.py          # users: platform, external_id, preferred_city_id, settings_json
│   │   ├── request_log.py   # request_logs: user_id, platform, action, city_id
│   │   └── usage_stats.py   # usage_stats: date, platform, total_requests, unique_users
│   ├── schemas/             # Pydantic v2 schemas для API запросов/ответов
│   ├── api/v1/              # Router-ы: weather, cities, sources, recommendations, users, admin
│   ├── services/            # Бизнес-логика
│   │   ├── weather_service.py      # Оркестрация: фетчеры + агрегатор + БД
│   │   ├── city_service.py         # Геокодинг через OpenWeatherMap Geocoding API
│   │   ├── source_manager.py       # Загрузка YAML-конфигов источников
│   │   ├── user_service.py         # CRUD пользователей
│   │   ├── stats_service.py        # Агрегация статистики использования
│   │   └── recommendation_service.py # Загрузка ML-модели, предсказание одежды
│   ├── fetchers/            # Модули сбора данных
│   │   ├── base.py          # AbstractWeatherFetcher (ABC): fetch_current(), fetch_forecast()
│   │   ├── openweathermap.py
│   │   ├── weatherapi.py
│   │   ├── yandex_weather.py
│   │   └── factory.py       # YAML config → экземпляр фетчера
│   └── aggregator/
│       ├── engine.py         # Взвешенное среднее, мода для нечисловых
│       └── normalizer.py     # Нормализация единиц к SI
├── config/
│   ├── settings.yaml
│   └── sources/             # YAML-конфиги для каждого источника
├── alembic/
└── tests/
```

## Правила

1. **Все I/O через async/await** — никаких синхронных HTTP-запросов или DB-операций
2. **Type hints обязательны** для всех функций
3. **SQLAlchemy 2.0 style**: `select()`, `Mapped[]`, `mapped_column()`, не legacy Query API
4. **Pydantic v2**: `model_validator`, `field_validator`, `ConfigDict`
5. **Все погодные значения в БД в SI**: Цельсий, м/с, гПа, мм — конвертация на фронтенде
6. **Логирование** через `logging.getLogger(__name__)`, не print()
7. **Обработка ошибок** при запросах к внешним API — try/except + логирование + fallback
8. **Конфиги источников** — YAML-файлы с подстановкой `${ENV_VAR}` и шаблонами `{city}`, `{date}`
9. **Аутентификация админа**: проверка заголовка `X-Admin-API-Key` через dependency injection

## API эндпоинты

- `GET /api/v1/weather/current?city_id=X` — агрегированная текущая погода
- `GET /api/v1/weather/forecast?city_id=X&days=N` — агрегированный прогноз
- `GET /api/v1/weather/current/by-source?city_id=X` — данные по каждому источнику
- `GET /api/v1/weather/chart/hourly?city_id=X` — точки графика на 24 часа
- `GET /api/v1/weather/chart/daily?city_id=X&days=N` — точки графика на N дней
- `GET /api/v1/cities/search?q=name` — поиск города (GeoCoding API)
- `GET /api/v1/sources` — список источников
- `POST /api/v1/users/identify` — создание/получение пользователя по cookie UUID
- `GET /api/v1/recommendations/clothing?city_id=X` — ML-рекомендации по одежде
- `GET /api/v1/admin/stats`, `GET /api/v1/admin/logs` — админ-панель (API-ключ)
- `GET /health`, `GET /readiness` — health checks

## Алгоритм агрегации

Числовые поля (temperature, feels_like, wind_speed, humidity, pressure, precipitation_amount, cloudiness):
```
weighted_avg = sum(value_i * priority_i) / sum(priority_i)
```

Нечисловые поля (precipitation_type, description):
```
mode(values); при равенстве частот — значение от источника с наивысшим приоритетом
```
