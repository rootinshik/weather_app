# Задачи проекта Weather Aggregator

Всего: 21 задача. Формат: каждую задачу можно скопировать как GitHub Issue.

---

## Задача 1: Инициализация проекта и структура монорепо

**Labels:** `devops`, `priority:high`
**Зависимости:** нет

### Описание

Создать базовую структуру монорепо для всех компонентов проекта: backend, frontend, bot, ml, docs.

### Что сделать

- [ ] Создать структуру каталогов:
  ```
  backend/app/{core,models,schemas,api/v1,services,fetchers,aggregator}/
  backend/{config/sources,alembic/versions,tests/}
  frontend/src/{pages,components,hooks,context,api,types,utils,styles}/
  bot/app/{handlers,keyboards,services,middlewares}/
  ml/{model,data,artifacts,tests}/
  ```
- [ ] Создать `.gitignore` (Python, Node.js, .env, артефакты ML)
- [ ] Создать `.env.example` с шаблоном переменных окружения
- [ ] Создать `README.md` (краткое описание + инструкция запуска)
- [ ] Создать `backend/requirements.txt`:
  ```
  fastapi>=0.109
  uvicorn[standard]>=0.27
  sqlalchemy[asyncio]>=2.0
  asyncpg>=0.29
  alembic>=1.13
  pydantic>=2.5
  pydantic-settings>=2.1
  pyyaml>=6.0
  aiohttp>=3.9
  beautifulsoup4>=4.12
  joblib>=1.3
  ```
- [ ] Создать `frontend/package.json` (React, TypeScript, Vite, Recharts, TanStack Query, React Router)
- [ ] Создать `bot/requirements.txt` (aiogram>=3.3, aiohttp, pyyaml)
- [ ] Создать `ml/requirements.txt` (scikit-learn, pandas, numpy, joblib)
- [ ] Все `__init__.py` файлы в Python-пакетах

### Acceptance Criteria

- `ls` показывает полную структуру каталогов
- Все requirements.txt содержат правильные зависимости
- .env.example содержит все необходимые переменные

---

## Задача 2: Docker Compose и Dockerfiles

**Labels:** `devops`, `priority:high`
**Зависимости:** Задача 1

### Описание

Настроить Docker-инфраструктуру для запуска всех сервисов одной командой.

### Что сделать

- [ ] Создать `docker-compose.yml` с сервисами:
  - `db`: postgres:16-alpine, healthcheck, volume pgdata
  - `backend`: build ./backend, depends_on db, ports 8000, volume ml/artifacts:ro
  - `frontend`: build ./frontend (multi-stage), ports 3000:80
  - `bot`: build ./bot, depends_on backend, no ports
  - `ml-train`: build ./ml, profile training
- [ ] Создать `backend/Dockerfile` (python:3.12-slim)
- [ ] Создать `frontend/Dockerfile` (node:20-alpine build → nginx:alpine)
- [ ] Создать `frontend/nginx.conf` (proxy /api → backend:8000, SPA fallback)
- [ ] Создать `bot/Dockerfile` (python:3.12-slim)
- [ ] Создать `ml/Dockerfile` (python:3.12-slim)
- [ ] Health checks для db и backend

### Acceptance Criteria

- `docker compose config` проходит без ошибок
- `docker compose build` собирает все образы

---

## Задача 3: Настройка базы данных и ORM-модели

**Labels:** `backend`, `priority:high`
**Зависимости:** Задача 1

### Описание

Настроить SQLAlchemy async, создать все ORM-модели и начальную миграцию Alembic.

### Что сделать

- [ ] `backend/app/core/database.py`:
  - async engine (create_async_engine)
  - async_sessionmaker
  - DeclarativeBase
- [ ] ORM-модели (SQLAlchemy 2.0, Mapped[], mapped_column()):
  - `models/city.py`: id, name, local_name, country, lat, lon, created_at
  - `models/source.py`: id, slug, display_name, source_type, priority, is_enabled, config_file
  - `models/weather.py`: id, city_id (FK), source_id (FK), record_type, forecast_dt, temperature, feels_like, wind_speed, wind_direction, humidity, pressure, precipitation_type, precipitation_amount, cloudiness, description, icon_code, fetched_at
  - `models/user.py`: id, platform, external_id, preferred_city_id (FK), settings_json (JSONB), created_at, last_active_at
  - `models/request_log.py`: id, user_id (FK), platform, action, city_id (FK), request_meta (JSONB), created_at
  - `models/usage_stats.py`: id, date, platform, total_requests, unique_users, city_queries_json (JSONB)
- [ ] Индексы и уникальные ограничения согласно system_design.md
- [ ] `alembic.ini` + `alembic/env.py` с async конфигурацией
- [ ] Начальная миграция `001_initial_schema.py`

### Acceptance Criteria

- `alembic upgrade head` успешно создаёт все таблицы
- `alembic downgrade base` откатывает миграцию
- Все FK-связи и индексы на месте

---

## Задача 4: Система конфигурации (YAML + Pydantic Settings)

**Labels:** `backend`, `priority:high`
**Зависимости:** Задача 1

### Описание

Реализовать загрузку настроек из YAML-файлов с подстановкой переменных окружения.

### Что сделать

- [ ] `backend/app/core/config.py`:
  - Pydantic Settings класс с загрузкой settings.yaml
  - Подстановка `${ENV_VAR}` в YAML-значениях
  - Поля: app, server, database, admin, scheduler, geocoding, ml
- [ ] `backend/app/services/source_manager.py`:
  - Загрузка всех YAML-файлов из `config/sources/`
  - Парсинг конфигурации источника (connection, endpoints/parsing, field_mapping)
  - Список доступных источников
- [ ] YAML-файлы:
  - `backend/config/settings.yaml` (основные настройки)
  - `backend/config/sources/openweathermap.yaml` (REST API, field_mapping)
  - `backend/config/sources/weatherapi.yaml` (REST API, unit_conversions)
  - `backend/config/sources/yandex_weather.yaml` (parser, selectors)
- [ ] `backend/app/dependencies.py` — get_settings(), get_db()

### Acceptance Criteria

- Config загружается корректно при старте приложения
- Подстановка ${ENV_VAR} работает
- Все три YAML-конфига источников парсятся без ошибок
- Отсутствующий env var → понятная ошибка при старте

---

## Задача 5: Базовый фетчер и фабрика фетчеров

**Labels:** `backend`, `priority:high`
**Зависимости:** Задача 4

### Описание

Создать абстракцию для сборщиков данных и фабрику, создающую фетчеры по YAML-конфигу.

### Что сделать

- [ ] `backend/app/fetchers/base.py`:
  ```python
  class AbstractWeatherFetcher(ABC):
      async def fetch_current(self, city: City) -> WeatherRecord | None
      async def fetch_forecast(self, city: City, days: int) -> list[WeatherRecord]
      async def test_connection(self) -> bool
  ```
- [ ] `backend/app/fetchers/factory.py`:
  - FetcherFactory: принимает YAML-конфиг, создаёт экземпляр фетчера по `source_type`
  - `api` → REST-фетчер, `parser` → HTML-фетчер
- [ ] `backend/app/aggregator/normalizer.py`:
  - Конвертации: kph→m/s, mph→m/s, F→C, K→C, mmHg→hPa
  - Маппинг `unit_conversions` из YAML

### Acceptance Criteria

- AbstractWeatherFetcher определяет полный контракт
- FetcherFactory создаёт корректный тип фетчера по конфигу
- Нормализатор правильно конвертирует все поддерживаемые единицы

---

## Задача 6: Фетчер OpenWeatherMap API

**Labels:** `backend`, `priority:high`
**Зависимости:** Задача 5

### Описание

Реализовать сборщик данных для OpenWeatherMap Current Weather и 5-Day Forecast API.

### Что сделать

- [ ] `backend/app/fetchers/openweathermap.py`:
  - Наследует AbstractWeatherFetcher
  - `fetch_current()`: GET /weather?q={city}&units=metric&appid={key}
  - `fetch_forecast()`: GET /forecast?q={city}&units=metric&appid={key}&cnt=40
  - Маппинг JSON-полей по field_mapping из YAML-конфига
  - Обработка ошибок: timeout, HTTP 4xx/5xx, невалидный JSON
  - Логирование через logging
- [ ] `test_connection()` — проверка доступности API

### Acceptance Criteria

- Корректно извлекает текущую погоду для произвольного города
- Корректно извлекает прогноз на 5 дней (3-часовые интервалы)
- Все поля маппятся в WeatherRecord
- При ошибке API — логирование + возврат None/пустого списка

### Затрагиваемые файлы

- `backend/app/fetchers/openweathermap.py` (новый)
- `backend/config/sources/openweathermap.yaml`

---

## Задача 7: Фетчер WeatherAPI.com

**Labels:** `backend`, `priority:medium`
**Зависимости:** Задача 5

### Описание

Реализовать сборщик данных для WeatherAPI.com Current и Forecast API.

### Что сделать

- [ ] `backend/app/fetchers/weatherapi.py`:
  - `fetch_current()`: GET /current.json?q={city}&key={key}
  - `fetch_forecast()`: GET /forecast.json?q={city}&key={key}&days=7
  - Конвертация: wind_kph → m/s (÷ 3.6)
  - Маппинг JSON-полей
  - Обработка ошибок, логирование

### Acceptance Criteria

- Корректно извлекает текущую погоду и прогноз на 7 дней
- Конвертация kph → m/s работает
- При ошибке API — логирование + graceful fallback

---

## Задача 8: Парсер Яндекс.Погоды (BeautifulSoup)

**Labels:** `backend`, `priority:medium`
**Зависимости:** Задача 5

### Описание

Реализовать HTML-парсер для Яндекс.Погоды через BeautifulSoup + CSS-селекторы.

### Что сделать

- [ ] `backend/app/fetchers/yandex_weather.py`:
  - `fetch_current()`: GET https://yandex.ru/pogoda/{city_slug}
  - Парсинг HTML через BeautifulSoup
  - CSS-селекторы из YAML-конфига (parsing.selectors)
  - Конвертация мм рт.ст. → гПа (× 1.333)
  - Обработка ошибок: таймаут, изменение HTML-структуры, отсутствие элементов
  - User-Agent заголовок
- [ ] Маппинг city_name → city_slug для URL

### Acceptance Criteria

- Парсинг HTML корректно извлекает температуру и другие показатели
- Конвертация mmHg → hPa работает
- При изменении HTML-структуры — понятная ошибка в логах
- CSS-селекторы берутся из YAML-конфига

---

## Задача 9: Движок агрегации данных

**Labels:** `backend`, `priority:high`
**Зависимости:** Задача 5

### Описание

Реализовать алгоритм суммирования данных из нескольких источников с учётом приоритетов.

### Что сделать

- [ ] `backend/app/aggregator/engine.py`:
  - `aggregate(records: list[WeatherRecord], priorities: dict[int, int]) -> AggregatedWeather`
  - Числовые поля: взвешенное среднее `Σ(value × priority) / Σ(priority)`
  - Нечисловые поля: мода, при равенстве частот → значение от источника с наивысшим приоритетом
  - Обработка отсутствующих данных (None → пропуск)
  - Список полей: temperature, feels_like, wind_speed, wind_direction, humidity, pressure, precipitation_type, precipitation_amount, cloudiness
- [ ] Pydantic-схема `AggregatedWeather`

### Acceptance Criteria

- Взвешенное среднее для 2-3 источников с разными приоритетами — правильный результат
- Мода для нечисловых полей работает корректно
- При одном источнике — его значения возвращаются без изменений
- None-значения корректно пропускаются

---

## Задача 10: Сервис погоды и планировщик

**Labels:** `backend`, `priority:high`
**Зависимости:** Задачи 6, 9

### Описание

Реализовать бизнес-логику получения и агрегации погоды, а также фоновый планировщик.

### Что сделать

- [ ] `backend/app/services/weather_service.py`:
  - `get_aggregated_current(city_id, source_slugs?)` — запрос из БД + агрегация
  - `get_aggregated_forecast(city_id, days, source_slugs?)`
  - `get_by_source(city_id)` — данные по каждому источнику отдельно
  - `get_chart_hourly(city_id)` — 24 точки (или с интервалом из конфига)
  - `get_chart_daily(city_id, days)` — min/max по дням
  - Если нет свежих данных (>30 мин) — триггер on-demand fetch
- [ ] `backend/app/core/scheduler.py`:
  - Запуск через asyncio.create_task в FastAPI lifespan
  - Периодический запрос для всех "отслеживаемых" городов (запрошенных за последние 24ч)
  - Интервал из config (scheduler.fetch_interval_minutes)
  - Логирование каждого цикла

### Acceptance Criteria

- `get_aggregated_current` возвращает агрегированные данные
- Планировщик запускается при старте приложения и работает в фоне
- On-demand fetch срабатывает при отсутствии свежих данных

---

## Задача 11: API эндпоинты — погода

**Labels:** `backend`, `priority:high`
**Зависимости:** Задача 10

### Описание

Создать REST API эндпоинты для получения погодных данных.

### Что сделать

- [ ] `backend/app/api/v1/weather.py`:
  - `GET /api/v1/weather/current` — query: city_id, sources (optional)
  - `GET /api/v1/weather/forecast` — query: city_id, days (3-7), sources
  - `GET /api/v1/weather/current/by-source` — query: city_id
  - `GET /api/v1/weather/chart/hourly` — query: city_id
  - `GET /api/v1/weather/chart/daily` — query: city_id, days
- [ ] `backend/app/schemas/weather.py`:
  - AggregatedWeatherResponse, ForecastResponse, SourceWeatherResponse
  - ChartPoint, DailyChartPoint
- [ ] `backend/app/api/router.py` — регистрация роутеров
- [ ] `backend/app/main.py` — FastAPI app с lifespan, CORS, router

### Acceptance Criteria

- Все 5 эндпоинтов отвечают корректным JSON
- Pydantic-валидация query-параметров работает
- CORS настроен для фронтенда
- OpenAPI документация доступна на /docs

---

## Задача 12: API эндпоинты — города, источники, пользователи

**Labels:** `backend`, `priority:medium`
**Зависимости:** Задачи 3, 4

### Описание

Создать REST API для работы с городами, источниками данных и пользователями.

### Что сделать

- [ ] `backend/app/api/v1/cities.py`:
  - `GET /api/v1/cities/search?q=name&limit=5` — поиск через OWM Geocoding API
  - `GET /api/v1/cities/{city_id}` — получение по ID
  - `POST /api/v1/cities` — upsert
- [ ] `backend/app/services/city_service.py`:
  - Проксирование запросов к OpenWeatherMap Geocoding API
  - Сохранение найденных городов в БД
- [ ] `backend/app/api/v1/sources.py`:
  - `GET /api/v1/sources` — список включённых
  - `GET /api/v1/sources/{slug}` — детали
- [ ] `backend/app/api/v1/users.py`:
  - `POST /api/v1/users/identify` — создание/получение по external_id + platform
  - `PATCH /api/v1/users/{user_id}/preferences` — обновление настроек
  - `GET /api/v1/users/{user_id}`
- [ ] `backend/app/services/user_service.py` — CRUD

### Acceptance Criteria

- Поиск города по названию возвращает результаты
- Пользователь создаётся при первом identify и возвращается при повторном
- Источники загружаются из YAML-конфигов

---

## Задача 13: API эндпоинты — админ + безопасность

**Labels:** `backend`, `priority:medium`
**Зависимости:** Задачи 3, 11

### Описание

Реализовать админ-API с аутентификацией по API-ключу, статистикой и логами.

### Что сделать

- [ ] `backend/app/core/security.py`:
  - Dependency `get_current_admin`: проверка заголовка X-Admin-API-Key
  - HTTPException 401 при невалидном ключе
- [ ] `backend/app/api/v1/admin.py`:
  - `POST /admin/auth` — валидация ключа
  - `GET /admin/stats?from_date&to_date&platform` — суточная статистика
  - `GET /admin/logs?limit&offset&platform&action` — логи с пагинацией
  - `GET /admin/sources` — все источники (включая отключённые)
  - `PATCH /admin/sources/{slug}` — toggle enabled/priority
  - `POST /admin/fetch-now` — принудительный запрос данных
- [ ] `backend/app/services/stats_service.py`:
  - Агрегация request_logs → usage_stats
  - Подсчёт уникальных пользователей по дням
- [ ] Middleware для логирования запросов в request_logs
- [ ] Health check эндпоинты: `GET /health`, `GET /readiness`

### Acceptance Criteria

- Админ-эндпоинты отвечают 401 без ключа и 200 с валидным ключом
- Статистика корректно агрегируется по дням и платформам
- Логи запросов записываются автоматически

---

## Задача 14: Генерация синтетического датасета для ML

**Labels:** `ml`, `priority:medium`
**Зависимости:** Задача 1

### Описание

Создать скрипт генерации синтетических данных для обучения модели рекомендаций по одежде.

### Что сделать

- [ ] `ml/model/labels.py`:
  - 8 категорий одежды с описанием и списком предметов (русский язык)
  - CLOTHING_CATEGORIES dict
- [ ] `ml/model/features.py`:
  - Определение 8 фичей: temperature, feels_like, wind_speed, humidity, pressure, precipitation_type, precipitation_amount, cloudiness
- [ ] `ml/generate_dataset.py`:
  - Генерация ~10000 строк
  - Правила назначения лейблов по температуре + осадкам
  - Поправка на ветер (wind_speed > 10 → эффективная t на 5°C ниже)
  - Гауссовский шум (σ=3°C) на границах категорий
  - Корреляции: зимние t → снег, летние → дождь
  - Сохранение в `data/synthetic_weather.csv`
- [ ] Визуализация распределения классов (опционально)

### Acceptance Criteria

- Датасет содержит ~10000 строк с 8 фичами + лейбл
- Все 8 категорий представлены
- Данные физически реалистичны (нет снега при +30°C)

---

## Задача 15: Обучение ML-модели и интеграция

**Labels:** `ml`, `backend`, `priority:medium`
**Зависимости:** Задачи 14, 11

### Описание

Обучить модель классификации и интегрировать с бэкендом.

### Что сделать

- [ ] `ml/model/pipeline.py`:
  - Pipeline: StandardScaler → RandomForestClassifier(n_estimators=100, max_depth=10, class_weight="balanced")
- [ ] `ml/train.py`:
  - Загрузка CSV
  - LabelEncoder для категорий
  - Train/test split 80/20
  - Обучение Pipeline
  - classification_report (print)
  - Сохранение model.joblib + label_encoder.joblib в artifacts/
- [ ] `backend/app/services/recommendation_service.py`:
  - Загрузка модели через joblib.load при старте
  - predict(weather) → category → description + items
- [ ] `backend/app/api/v1/recommendations.py`:
  - `GET /api/v1/recommendations/clothing?city_id=X`
- [ ] `backend/app/schemas/recommendation.py`

### Acceptance Criteria

- `docker compose --profile training run ml-train` обучает модель и сохраняет артефакты
- classification_report показывает accuracy > 85%
- Эндпоинт /recommendations/clothing возвращает корректную рекомендацию

---

## Задача 16: Telegram-бот — настройка и базовые команды

**Labels:** `bot`, `priority:medium`
**Зависимости:** Задача 12

### Описание

Настроить aiogram 3 Telegram-бота с базовой инфраструктурой.

### Что сделать

- [ ] `bot/app/main.py` — entry point, Bot + Dispatcher + start_polling
- [ ] `bot/app/config.py` — загрузка bot_settings.yaml
- [ ] `bot/app/bot.py` — создание Bot и Dispatcher
- [ ] `bot/app/services/api_client.py`:
  - BackendAPIClient(base_url) с aiohttp.ClientSession
  - Методы: get_current_weather, get_forecast, search_cities, identify_user, update_preferences, get_recommendation, get_sources
- [ ] `bot/app/middlewares/user_tracking.py`:
  - При каждом сообщении → POST /users/identify
- [ ] `bot/app/handlers/start.py` — /start: приветствие, регистрация
- [ ] `bot/app/handlers/help.py` — /help: список команд
- [ ] `bot/config/bot_settings.yaml`

### Acceptance Criteria

- Бот запускается и отвечает на /start и /help
- API-клиент корректно обращается к бэкенду
- Пользователь регистрируется в бэкенде при /start

---

## Задача 17: Telegram-бот — команды погоды и управления

**Labels:** `bot`, `priority:medium`
**Зависимости:** Задача 16

### Описание

Реализовать основные команды бота: погода, прогноз, город, источники.

### Что сделать

- [ ] `bot/app/handlers/weather.py`:
  - `/weather [город]` — текущая погода + рекомендация по одежде
  - Если город не указан — использовать город по умолчанию
  - Форматирование с emoji (☀️🌧❄️💨)
- [ ] `bot/app/handlers/forecast.py`:
  - `/forecast [город]` — прогноз на 3-7 дней
  - Таблица: дата | t min/max | осадки | иконка
- [ ] `bot/app/handlers/city.py`:
  - `/city` — список городов (inline-клавиатура)
  - `/city <город>` — установка города по умолчанию
- [ ] `bot/app/handlers/source.py`:
  - `/source` — список источников с id, статусом, приоритетом
  - `/source <id> <приоритет>` — настройка источника
- [ ] `bot/app/services/formatters.py`:
  - format_current_weather(data) → текст с emoji
  - format_forecast(data) → таблица по дням
  - format_recommendation(data) → текст рекомендации
- [ ] `bot/app/keyboards/inline.py`:
  - Клавиатура выбора города (результаты поиска)
  - Клавиатура управления источниками

### Acceptance Criteria

- /weather показывает текущую погоду с emoji и рекомендацией
- /forecast показывает прогноз на 3 дня
- /city позволяет установить город по умолчанию
- /source показывает и позволяет менять источники

---

## Задача 18: Фронтенд — инициализация и Layout

**Labels:** `frontend`, `priority:medium`
**Зависимости:** Задача 11

### Описание

Создать React + TypeScript проект с базовой инфраструктурой.

### Что сделать

- [ ] Инициализация Vite + React + TypeScript проекта
- [ ] `frontend/vite.config.ts` (proxy /api → localhost:8000)
- [ ] `frontend/tsconfig.json` (strict: true)
- [ ] React Router: маршруты /, /forecast, /admin, *
- [ ] `src/App.tsx` — Root с провайдерами контекстов
- [ ] Контексты:
  - `src/context/ThemeContext.tsx` — "light" | "dark", localStorage
  - `src/context/UnitsContext.tsx` — {temperature, wind, pressure}, localStorage
  - `src/context/UserContext.tsx` — {userId, externalId}, cookie
- [ ] `src/api/client.ts` — базовый HTTP-клиент (fetch wrapper)
- [ ] Layout:
  - `src/components/layout/Header.tsx` — заглушки для CitySearch, ThemeToggle, UnitSelector
  - `src/components/layout/Footer.tsx`
  - `src/components/layout/Layout.tsx` — обёртка
- [ ] `src/styles/globals.css` — CSS variables для dark/light тем
- [ ] TypeScript интерфейсы в `src/types/`
- [ ] `src/utils/unitConversion.ts`:
  - celsiusToFahrenheit, celsiusToKelvin
  - msToKmh, msToMph
  - hpaToMmhg
- [ ] `src/utils/cookies.ts` — getCookie, setCookie

### Acceptance Criteria

- `npm run dev` запускает приложение без ошибок
- Маршрутизация работает (/, /forecast, /admin)
- Тема переключается (dark/light)
- Cookie UUID генерируется при первом визите

---

## Задача 19: Фронтенд — страницы погоды

**Labels:** `frontend`, `priority:medium`
**Зависимости:** Задача 18

### Описание

Реализовать основные страницы отображения погоды.

### Что сделать

- [ ] API-хуки:
  - `src/hooks/useWeather.ts` (TanStack Query)
  - `src/hooks/useForecast.ts`
  - `src/hooks/useCitySearch.ts` (debounced)
- [ ] API-клиенты:
  - `src/api/weather.ts`
  - `src/api/cities.ts`
  - `src/api/recommendations.ts`
- [ ] HomePage (`src/pages/HomePage.tsx`):
  - `CurrentWeather` — карточка текущей погоды (все показатели)
  - `ClothingRecommendation` — ML-рекомендация
  - `TemperatureChart` (mode=hourly) — Recharts LineChart на 24 часа
  - `ForecastList` (days=3) — компактный прогноз
- [ ] ForecastPage (`src/pages/ForecastPage.tsx`):
  - `ForecastDaySlider` — выбор 3-7 дней
  - `ForecastList` (days=3-7) — карточки по дням
  - `TemperatureChart` (mode=daily) — min/max график
- [ ] Компоненты:
  - `WeatherIcon` — маппинг условий → иконки/SVG
  - `ForecastCard` — карточка одного дня (min/max, иконка, осадки)
- [ ] Конвертация единиц через UnitsContext + unitConversion.ts

### Acceptance Criteria

- HomePage отображает текущую погоду, рекомендацию, график 24ч, прогноз 3 дня
- ForecastPage отображает расширенный прогноз с графиком
- Единицы измерения переключаются в реальном времени
- Графики Recharts рендерятся корректно

---

## Задача 20: Фронтенд — контролы и админ-панель

**Labels:** `frontend`, `priority:low`
**Зависимости:** Задача 19

### Описание

Реализовать элементы управления и минимальную админ-панель.

### Что сделать

- [ ] `CitySearch` (`src/components/controls/CitySearch.tsx`):
  - Autocomplete с debounce (300мс)
  - Выпадающий список результатов
  - Сохранение выбранного города в localStorage
  - Избранные города
- [ ] `UnitSelector` (`src/components/controls/UnitSelector.tsx`):
  - Dropdown для температуры: °C / °F / K
  - Dropdown для ветра: м/с / км/ч / мили/ч
  - Dropdown для давления: гПа / мм рт.ст.
- [ ] `ThemeToggle` (`src/components/controls/ThemeToggle.tsx`):
  - Кнопка переключения dark/light
  - Иконка солнца/луны
- [ ] `SourceSelector` (`src/components/controls/SourceSelector.tsx`):
  - Переключатели для каждого источника
  - Отображение приоритета
- [ ] AdminPage (`src/pages/AdminPage.tsx`):
  - `AdminLogin` — форма ввода API-ключа
  - `StatsPanel` — таблица статистики (дата, платформа, запросы, пользователи)
  - `LogsPanel` — таблица логов с пагинацией (offset/limit)
  - Фильтры по дате и платформе

### Acceptance Criteria

- Поиск города работает с autocomplete и debounce
- Единицы измерения сохраняются в localStorage
- Тема переключается и сохраняется
- Админ-панель доступна после ввода API-ключа
- Статистика и логи отображаются в таблицах

---

## Задача 21: Интеграционное тестирование и финализация

**Labels:** `devops`, `priority:low`
**Зависимости:** Все предыдущие

### Описание

Проверить работоспособность всей системы в Docker Compose, финализировать документацию.

### Что сделать

- [ ] `docker compose up --build` — все сервисы стартуют без ошибок
- [ ] Проверить цепочку:
  1. `curl http://localhost:8000/health` → 200
  2. `curl http://localhost:8000/api/v1/cities/search?q=Moscow` → список городов
  3. `curl http://localhost:8000/api/v1/weather/current?city_id=1` → агрегированная погода
  4. `curl http://localhost:8000/api/v1/recommendations/clothing?city_id=1` → рекомендация
  5. Открыть http://localhost:3000 → веб-интерфейс работает
  6. /weather в Telegram-боте → ответ с погодой
- [ ] nginx конфигурация: /api проксируется на бэкенд
- [ ] Финализация README.md:
  - Описание проекта
  - Стек
  - Инструкция запуска
  - Скриншоты (опционально)
- [ ] Проверить .gitignore: .env, __pycache__, node_modules, артефакты ML

### Acceptance Criteria

- Все 4 сервиса (db, backend, frontend, bot) работают одновременно
- E2E цепочка проходит без ошибок
- README содержит актуальную инструкцию запуска
