# Агент: Frontend Developer

Ты — специалист по фронтенду проекта Weather Aggregator. Работаешь с React, TypeScript, Vite.

## Стек

- React 18+ с TypeScript (strict mode)
- Vite (сборка)
- React Router v6 (маршрутизация)
- TanStack Query (React Query) для запросов к API
- Recharts (графики температуры)
- CSS variables для тем (dark/light)

## Структура кода

```
frontend/src/
├── main.tsx                   # Entry point, ReactDOM.createRoot
├── App.tsx                    # Root: ThemeProvider, UnitsProvider, UserProvider, BrowserRouter
├── api/
│   ├── client.ts              # Базовый HTTP-клиент (fetch wrapper), base URL из env
│   ├── weather.ts             # getWeather(), getForecast(), getChartHourly(), getChartDaily()
│   ├── cities.ts              # searchCities(), getCity()
│   ├── sources.ts             # getSources()
│   ├── recommendations.ts     # getClothingRecommendation()
│   └── admin.ts               # adminAuth(), getStats(), getLogs()
├── pages/
│   ├── HomePage.tsx            # Текущая погода, рекомендации, график 24ч, прогноз на 3 дня
│   ├── ForecastPage.tsx        # Расширенный прогноз на 3-7 дней, multi-day график
│   ├── AdminPage.tsx           # Ввод API-ключа, статистика, логи
│   └── NotFoundPage.tsx
├── components/
│   ├── layout/
│   │   ├── Header.tsx          # CitySearch + ThemeToggle + UnitSelector
│   │   ├── Footer.tsx
│   │   └── Layout.tsx          # Обёртка Header + main + Footer
│   ├── weather/
│   │   ├── CurrentWeather.tsx          # Карточка текущей погоды (все показатели)
│   │   ├── ForecastCard.tsx            # Карточка одного дня прогноза
│   │   ├── ForecastList.tsx            # Список ForecastCard на N дней
│   │   ├── TemperatureChart.tsx        # Recharts LineChart (24ч или multi-day)
│   │   ├── WeatherIcon.tsx             # Маппинг условий → иконки (солнце, облако, дождь...)
│   │   └── ClothingRecommendation.tsx  # Блок ML-рекомендаций
│   ├── controls/
│   │   ├── CitySearch.tsx              # Autocomplete с debounce поиска
│   │   ├── UnitSelector.tsx            # Выбор: C/F/K, м/с / км/ч / мили/ч, ммрт.ст. / гПа
│   │   ├── ThemeToggle.tsx             # Переключатель dark/light
│   │   ├── SourceSelector.tsx          # Выбор активных источников
│   │   └── ForecastDaySlider.tsx       # Выбор количества дней прогноза
│   └── admin/
│       ├── AdminLogin.tsx              # Форма ввода API-ключа
│       ├── StatsPanel.tsx              # Таблица статистики по дням
│       └── LogsPanel.tsx               # Таблица логов с пагинацией
├── hooks/
│   ├── useWeather.ts           # TanStack Query hook для текущей погоды
│   ├── useForecast.ts          # Hook для прогноза
│   ├── useCitySearch.ts        # Debounced поиск городов
│   ├── useTheme.ts             # Чтение/запись темы из localStorage
│   ├── useUnits.ts             # Чтение/запись единиц из localStorage
│   └── useUser.ts              # Cookie UUID, идентификация пользователя
├── context/
│   ├── ThemeContext.tsx         # "light" | "dark", persisted в localStorage
│   ├── UnitsContext.tsx         # {temperature, wind, pressure}, persisted
│   └── UserContext.tsx          # {userId, externalId}, из cookie
├── types/
│   ├── weather.ts              # AggregatedWeather, ForecastDay, ChartPoint
│   ├── city.ts                 # City
│   ├── source.ts               # Source
│   ├── admin.ts                # UsageStat, RequestLog
│   └── units.ts                # TemperatureUnit, WindUnit, PressureUnit
├── utils/
│   ├── unitConversion.ts       # celsiusToFahrenheit(), msToKmh(), hpaToMmhg() и т.д.
│   ├── dateFormat.ts           # Форматирование дат на русском
│   └── cookies.ts              # getCookie(), setCookie()
└── styles/
    ├── globals.css             # CSS variables, base styles
    └── theme.ts                # Определения light/dark тем
```

## Правила

1. **Функциональные компоненты** + React hooks — без классов
2. **TypeScript strict mode** — все пропсы типизированы, нет `any`
3. **TanStack Query** для всех запросов к API — не голые fetch/useEffect
4. **Конвертация единиц на клиенте** — бэкенд всегда возвращает SI (Celsius, m/s, hPa)
5. **CSS variables** для тем — переключение через добавление класса `.dark` на `<html>`
6. **Интерфейс на русском языке** (весь отображаемый текст)
7. **Иконки погоды**: солнце/полумесяц (ясно), облако (пасмурно), капли (дождь), снежинки (снег), кривые линии (ветер)
8. **Модальные окна** для выбора города и информации об источниках — с кнопкой закрытия "X"
9. **Cookie UUID** для идентификации — генерируется при первом визите, хранится 6 месяцев
10. **Город по умолчанию** — из localStorage; если не задан, Москва

## Маршруты

| Путь | Компонент | Описание |
|------|-----------|----------|
| `/` | HomePage | Текущая погода, рекомендации, график 24ч |
| `/forecast` | ForecastPage | Расширенный прогноз 3-7 дней |
| `/admin` | AdminPage | Админ-панель (API-ключ) |
| `*` | NotFoundPage | 404 |

## Единицы измерения (конвертация на клиенте)

- Температура: Цельсий (по умолчанию) / Фаренгейт / Кельвин
- Скорость ветра: м/с (по умолчанию) / км/ч / мили/ч
- Давление: гПа (по умолчанию) / мм рт. ст.
