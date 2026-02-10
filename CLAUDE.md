# Weather Aggregator — Проект интернет-сервиса наблюдения за погодой

## Описание

Учебный проект СПбПУ (дисциплина «Технологии разработки качественного ПО»). Сервис агрегирует данные о погоде из нескольких источников, суммирует их с учётом приоритетов, визуализирует через веб-интерфейс и Telegram-бота, даёт ML-рекомендации по одежде и аксессуарам.

## Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Бэкенд | Python 3.12, FastAPI, async/await |
| ORM | SQLAlchemy 2.0 (async) + Alembic (миграции) |
| База данных | PostgreSQL 16 |
| Фронтенд | React 18+ с TypeScript, Vite, Recharts (графики), TanStack Query |
| Telegram-бот | aiogram 3 |
| ML | scikit-learn (RandomForestClassifier), синтетический датасет |
| Парсинг | BeautifulSoup 4, aiohttp |
| HTTP-клиент | aiohttp (async) |
| Конфигурация | YAML-файлы |
| Деплой | Docker Compose |

## Структура монорепо

```
trkpo/
├── backend/          # FastAPI бэкенд (Python)
│   ├── app/          # Исходный код приложения
│   │   ├── api/v1/   # REST API эндпоинты
│   │   ├── core/     # Конфигурация, БД, безопасность, планировщик
│   │   ├── models/   # SQLAlchemy ORM-модели
│   │   ├── schemas/  # Pydantic-схемы запросов/ответов
│   │   ├── services/ # Бизнес-логика
│   │   ├── fetchers/ # Модули сбора данных из источников
│   │   └── aggregator/ # Движок агрегации (взвешенное среднее)
│   ├── config/       # YAML-конфиги
│   │   ├── settings.yaml
│   │   └── sources/  # Конфиги источников данных
│   ├── alembic/      # Миграции БД
│   └── tests/
├── frontend/         # React + TypeScript SPA
│   └── src/
│       ├── pages/    # HomePage, ForecastPage, AdminPage
│       ├── components/ # UI-компоненты
│       ├── hooks/    # React hooks
│       ├── context/  # ThemeContext, UnitsContext, UserContext
│       ├── api/      # HTTP-клиент к бэкенду
│       ├── types/    # TypeScript интерфейсы
│       └── utils/    # Конвертация единиц, форматирование
├── bot/              # Telegram-бот (aiogram 3)
│   └── app/
│       ├── handlers/ # Обработчики команд
│       ├── keyboards/ # Inline/Reply клавиатуры
│       ├── services/ # API-клиент к бэкенду
│       └── middlewares/
├── ml/               # ML-модель рекомендаций
│   ├── generate_dataset.py  # Генерация синтетических данных
│   ├── train.py              # Обучение модели
│   ├── model/                # Pipeline, фичи, лейблы
│   ├── data/                 # CSV-датасет
│   └── artifacts/            # model.joblib, label_encoder.joblib
├── docs/             # Документация
│   ├── functional_specification.pdf
│   └── system_design.md
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Команды

```bash
# Запуск всех сервисов (db, backend, frontend, bot)
docker compose up

# Запуск с пересборкой образов
docker compose up --build

# Обучение ML-модели (одноразовый запуск)
docker compose --profile training run ml-train

# Миграции БД (внутри контейнера backend)
docker compose exec backend alembic upgrade head

# Создание новой миграции
docker compose exec backend alembic revision --autogenerate -m "описание"
```

## Соглашения по коду

### Python (backend, bot, ml)
- PEP 8, максимальная длина строки: 100 символов
- Все I/O-операции через async/await
- Type hints обязательны для аргументов функций и возвращаемых значений
- Pydantic v2 для валидации данных (schemas)
- SQLAlchemy 2.0 style (select(), Mapped[], mapped_column())
- Логирование через стандартный модуль `logging` (не print)

### TypeScript (frontend)
- Строгий режим TypeScript (strict: true)
- Функциональные компоненты + React hooks (без классовых компонентов)
- TanStack Query для всех запросов к API (кеширование, refetch)
- CSS variables для тем (dark/light)
- Конвертация единиц измерения на клиенте (utils/unitConversion.ts)

### Конфигурация источников данных
- Формат: YAML-файлы в `backend/config/sources/`
- Шаблоны URL: `{city}`, `{date}`, `{api_key}` — подстановка при запросе
- Переменные окружения в YAML: `${OWM_API_KEY}` — подстановка при загрузке
- Каждый источник: отдельный YAML-файл с маппингом полей

### База данных
- Все значения хранятся в единицах SI: Цельсий, м/с, гПа, мм
- Конвертация в другие единицы (Фаренгейт, км/ч, ммрт.ст.) — на фронтенде
- Таблицы: cities, weather_sources, weather_records, users, request_logs, usage_stats

## Архитектурные решения

- **Бот и фронтенд общаются с бэкендом только через REST API** — бот не обращается к БД напрямую
- **Периодический сбор данных** — asyncio background tasks внутри процесса FastAPI (не Celery)
- **Аутентификация админа** — API-ключ в заголовке `X-Admin-API-Key` (задаётся в .env)
- **Идентификация пользователей веб-версии** — анонимно, через UUID v4 в cookie (срок: 6 месяцев)
- **Идентификация пользователей Telegram** — chat_id мессенджера
- **Темы интерфейса** — простой dark/light toggle через CSS variables
- **Hot reload конфигов** — не реализуется, изменения применяются при перезапуске контейнера
- **Алгоритм агрегации**: взвешенное среднее (вес = приоритет) для числовых, мода для нечисловых

## Источники данных (демо)

1. **OpenWeatherMap** (REST API, JSON) — текущая погода + прогноз на 5 дней
2. **WeatherAPI.com** (REST API, JSON) — текущая погода + прогноз на 7 дней
3. **Яндекс.Погода** (HTML-парсинг, BeautifulSoup) — демонстрация парсинга

## Переменные окружения (.env)

```
DB_USER=weather
DB_PASSWORD=weather_secret
DB_HOST=db
DB_PORT=5432
DB_NAME=weather_db
OWM_API_KEY=your_openweathermap_api_key
WEATHERAPI_KEY=your_weatherapi_com_key
ADMIN_API_KEY=your_admin_secret_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

## Полезные ссылки

- [Функциональная спецификация](docs/functional_specification.pdf)
- [System Design](docs/system_design.md)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [WeatherAPI.com](https://www.weatherapi.com/docs/)
