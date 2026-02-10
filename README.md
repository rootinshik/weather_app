# Weather Aggregator

Сервис агрегации данных о погоде из нескольких источников с веб-интерфейсом, Telegram-ботом и ML-рекомендациями по одежде.

Учебный проект СПбПУ, дисциплина «Технологии разработки качественного ПО».

## Стек

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL 16
- **Frontend:** React 18+, TypeScript, Vite, Recharts, TanStack Query
- **Bot:** aiogram 3, aiohttp
- **ML:** scikit-learn (RandomForestClassifier)

## Быстрый старт

1. Скопируйте `.env.example` в `.env` и заполните переменные:
   ```bash
   cp .env.example .env
   ```

2. Запустите все сервисы:
   ```bash
   docker compose up --build
   ```

3. Примените миграции БД:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

4. Обучите ML-модель (одноразово):
   ```bash
   docker compose --profile training run ml-train
   ```

## Структура проекта

```
weather_app/
├── backend/    # FastAPI бэкенд
├── frontend/   # React SPA
├── bot/        # Telegram-бот
├── ml/         # ML-модель рекомендаций
└── docs/       # Документация
```

## Переменные окружения

См. [.env.example](.env.example) для полного списка необходимых переменных.
