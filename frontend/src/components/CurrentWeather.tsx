import { Wind, Droplets, Thermometer, Gauge } from "lucide-react";
import { WeatherIcon } from "./WeatherIcon";
import { useUnits } from "../context/UnitContext";
import {
  convertTemperature,
  convertWind,
  convertPressure,
} from "../utils/unitConversions";

export interface AggregatedWeather {
  temperature: number;
  feels_like: number;
  humidity: number;
  wind_speed: number;
  pressure: number;
  precipitation_amount?: number | null;
  description?: string | null;
}

export interface CurrentWeatherResponse {
  city_id: number;
  fetched_at: string;
  weather: AggregatedWeather;
}

interface CurrentWeatherProps {
  data?: CurrentWeatherResponse;
  isLoading: boolean;
  isError?: boolean;
}

export function CurrentWeather({
  data,
  isLoading,
  isError,
}: CurrentWeatherProps) {
  const { tempUnit, windUnit, pressureUnit } = useUnits();

  if (isError) {
    return (
      <div className="glass p-6 rounded-2xl border border-red-500">
        <p className="text-red-500">Ошибка загрузки текущей погоды</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="glass p-6 rounded-2xl">
        <p className="text-muted">Загрузка погоды...</p>
      </div>
    );
  }

  if (!data?.weather) {
    return (
      <div className="glass p-6 rounded-2xl">
        <p className="text-muted">Нет данных о погоде</p>
      </div>
    );
  }

  const weather = data.weather;

  const temp = convertTemperature(weather.temperature, tempUnit);
  const feels = convertTemperature(weather.feels_like, tempUnit);
  const wind = convertWind(weather.wind_speed, windUnit);
  const pressure = convertPressure(weather.pressure, pressureUnit);

  // ⭐ Russian weather description
  const weatherTranslations: Record<string, string> = {
    "clear sky": "Ясно",
    "few clouds": "Небольшая облачность",
    "scattered clouds": "Рассеянные облака",
    "broken clouds": "Облачно",
    "overcast clouds": "Пасмурно",
    "light rain": "Небольшой дождь",
    "moderate rain": "Дождь",
    "heavy rain": "Сильный дождь",
    "light snow": "Небольшой снег",
    "snow": "Снег",
    "mist": "Туман",
    "fog": "Туман",
  };

  const descriptionRu =
    weatherTranslations[weather.description?.toLowerCase() ?? ""] ??
    weather.description;

  // ⭐ City name from saved cities
  const savedCities = JSON.parse(localStorage.getItem("cities") || "[]");
  const city = savedCities.find((c: any) => c.id === data.city_id);
  const cityName = city ? city.name : "Город";

  return (
    <div className="glass p-6 rounded-2xl shadow-lg">

      <h2 className="text-2xl font-semibold mb-6">{cityName}</h2>

      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-5xl font-bold">
            {Math.round(temp)}°{tempUnit}
          </p>

          <p className="text-muted text-lg">
            Ощущается как {Math.round(feels)}°{tempUnit}
          </p>

          {descriptionRu && (
            <p className="text-muted capitalize mt-1">
              {descriptionRu}
            </p>
          )}
        </div>

        <WeatherIcon
          condition={weather.description ?? undefined}
          size={64}
        />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">

        <div className="flex items-center gap-2">
          <Wind className="w-4 h-4 text-accent" />
          <span>{wind.toFixed(1)} {windUnit === "m/s" ? "м/с" : "км/ч"}</span>
        </div>

        <div className="flex items-center gap-2">
          <Droplets className="w-4 h-4 text-accent" />
          <span>Влажность: {weather.humidity}%</span>
        </div>

        <div className="flex items-center gap-2">
          <Gauge className="w-4 h-4 text-accent" />
          <span>Давление: {pressure.toFixed(0)} {pressureUnit === "hPa" ? "гПа" : "мм рт.ст."}</span>
        </div>

        <div className="flex items-center gap-2">
          <Thermometer className="w-4 h-4 text-accent" />
          <span>
            {weather.precipitation_amount
              ? `${weather.precipitation_amount} мм`
              : "Без осадков"}
          </span>
        </div>

      </div>

      <p className="text-xs text-muted mt-6">
        Обновлено: {new Date(data.fetched_at).toLocaleString("ru-RU")}
      </p>

    </div>
  );
}