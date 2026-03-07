import { useUnits } from "../context/UnitContext";
import {
  convertTemperature,
  convertWind,
} from "../utils/unitConversions";

interface ForecastItem {
  forecast_dt: string;
  weather: {
    temperature?: number;
    humidity?: number;
    wind_speed?: number;
  };
}

interface ForecastResponse {
  city_id: number;
  days: number;
  forecasts: ForecastItem[];
}

interface Props {
  data?: ForecastResponse;
  isLoading: boolean;
}

export function ForecastList({ data, isLoading }: Props) {

  const { tempUnit, windUnit } = useUnits();

  if (isLoading) {
    return <p>Загрузка прогноза...</p>;
  }

  if (!data || !data.forecasts || data.forecasts.length === 0) {
    return <p>Прогноз недоступен</p>;
  }

  // ⭐ group forecasts by day
  const dailyMap: Record<string, ForecastItem> = {};

  data.forecasts.forEach((item) => {
    const date = new Date(item.forecast_dt).toDateString();

    if (!dailyMap[date]) {
      dailyMap[date] = item;
    }
  });

  const dailyForecasts = Object.values(dailyMap).slice(0, 3);

  return (
    <div className="grid md:grid-cols-3 gap-4">

      {dailyForecasts.map((item, index) => {

        const date = new Date(item.forecast_dt);

        const temp =
          item.weather.temperature != null
            ? convertTemperature(
                item.weather.temperature,
                tempUnit as any   // ⭐ allow C/F/K
              )
            : null;

        const wind =
          item.weather.wind_speed != null
            ? convertWind(
                item.weather.wind_speed,
                windUnit as any   // ⭐ allow m/s km/h mph
              )
            : null;

        return (
          <div key={index} className="glass rounded-2xl p-5 space-y-2">

            <h4 className="font-semibold">
              {date.toLocaleDateString("ru-RU", {
                weekday: "short",
                day: "numeric",
                month: "short",
              })}
            </h4>

            <div className="text-2xl font-bold">
              {temp != null ? `${Math.round(temp)}°${tempUnit}` : "--"}
            </div>

            <div className="text-sm text-muted">

              <p>
                Влажность: {item.weather.humidity ?? "--"}%
              </p>

              <p>
                Ветер: {wind != null
<<<<<<< HEAD
                  ? `${wind.toFixed(1)} ${windUnit}`
=======
                  ? `${wind.toFixed(1)} ${windUnit === "m/s" ? "м/с" : "км/ч"}`
>>>>>>> 4b2fc05796ea401268e216a0370a4b6691228d9d
                  : "--"}
              </p>

            </div>

          </div>
        );

      })}

    </div>
  );
}