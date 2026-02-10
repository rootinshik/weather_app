# Руководство по локальной разработке

## Требования

| Инструмент | Версия | Установка |
|-----------|--------|-----------|
| Python | 3.12+ | [python.org](https://www.python.org/downloads/) |
| uv | latest | `pip install uv` или [docs.astral.sh](https://docs.astral.sh/uv/getting-started/installation/) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) |
| Docker + Compose | latest | [docker.com](https://www.docker.com/) |

## Быстрая настройка

Скрипты создают `.venv` в каждой папке сервиса, устанавливают зависимости и создают `.env` из примера.

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

**Linux / macOS:**
```bash
bash setup.sh
```

После этого заполни API-ключи в `.env`.

## Ручная настройка

Если хочешь настроить только один сервис:

```bash
# Backend
cd backend && uv venv && uv pip install -e . && cd ..

# Bot
cd bot && uv venv && uv pip install -e . && cd ..

# ML
cd ml && uv venv && uv pip install -e . && cd ..

# Frontend
cd frontend && npm install && cd ..
```

## Запуск сервисов локально

### База данных (через Docker)

Проще всего поднять только PostgreSQL, не поднимая все остальное:

```bash
docker compose up db -d
```

### Backend

```bash
# DB_HOST=localhost, потому что в .env стоит "db" (имя docker-сервиса)
DB_HOST=localhost cd backend && uv run uvicorn app.main:app --reload --port 8000
```

Или создай `backend/.env.local` с `DB_HOST=localhost` — pydantic-settings его подхватит.

После запуска:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

### Frontend

```bash
cd frontend && npm run dev
```

Dev-сервер запустится на http://localhost:5173 с hot-reload.

### Telegram-бот

```bash
cd bot && TELEGRAM_BOT_TOKEN=<токен> uv run python -m app.main
```

### ML

```bash
cd ml
uv run python generate_dataset.py   # генерация синтетических данных
uv run python train.py              # обучение модели
```

## Миграции БД

```bash
# Применить все миграции
cd backend && uv run alembic upgrade head

# Откатить все
uv run alembic downgrade base

# Создать новую миграцию после изменения моделей
uv run alembic revision --autogenerate -m "описание изменений"
```

## VS Code

### Расширения

При открытии проекта VS Code предложит установить рекомендованные расширения (`.vscode/extensions.json`):

| Расширение | Назначение |
|-----------|-----------|
| Python + Pylance | Подсветка, автодополнение, type checking |
| Ruff | Линтер и форматтер для Python |
| Prettier | Форматтер для TypeScript/React |
| Docker | Работа с Dockerfile и docker-compose |
| Even Better TOML | Подсветка `pyproject.toml` |

### Выбор интерпретатора Python

1. `Ctrl+Shift+P` → **Python: Select Interpreter**
2. Выбрать интерпретатор в зависимости от того, над каким сервисом работаешь:
   - Backend: `backend/.venv/Scripts/python.exe` (Windows) или `backend/.venv/bin/python`
   - Bot: `bot/.venv/...`
   - ML: `ml/.venv/...`

> Pylance автоматически подхватывает нужный venv при открытии файлов из `backend/`, `bot/`, `ml/` благодаря `pyrightconfig.json` в каждой папке.

## Управление зависимостями

> **Никогда не редактировать `requirements.txt` вручную** — он генерируется автоматически.

Добавить зависимость в сервис:
```bash
# 1. Добавить в pyproject.toml секцию [project].dependencies
# 2. Переустановить
cd backend && uv pip install -e .

# 3. Обновить requirements.txt для Docker-образа
uv pip compile pyproject.toml -o requirements.txt
```

## Git-процесс

1. Для каждого GitHub issue создаётся отдельная ветка:
   ```bash
   git checkout -b feature/issue-<номер>-краткое-описание
   ```
2. Работа ведётся в ветке.
3. Мерж в `main` — только через Pull Request.

## Переменные окружения

| Переменная | Описание | Пример |
|-----------|---------|--------|
| `DB_USER` | Пользователь PostgreSQL | `weather` |
| `DB_PASSWORD` | Пароль PostgreSQL | `weather_secret` |
| `DB_HOST` | Хост БД (в Docker: `db`, локально: `localhost`) | `localhost` |
| `DB_PORT` | Порт PostgreSQL | `5432` |
| `DB_NAME` | Имя базы данных | `weather_db` |
| `OWM_API_KEY` | OpenWeatherMap API key | — |
| `WEATHERAPI_KEY` | WeatherAPI.com key | — |
| `ADMIN_API_KEY` | Секретный ключ для admin-эндпоинтов | — |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота | — |
