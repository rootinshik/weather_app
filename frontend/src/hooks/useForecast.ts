import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/apiClient";

interface ForecastItem {
  forecast_dt: string;
  weather: {
    temperature?: number;
    feels_like?: number;
    humidity?: number;
    wind_speed?: number;
  };
}

export interface ForecastResponse {
  city_id: number;
  days: number;
  forecasts: ForecastItem[];
}

export const useForecast = (cityId: number, days: number) => {
  return useQuery<ForecastResponse>({
    queryKey: ["forecast", cityId, days],
    queryFn: () =>
      apiClient.get<ForecastResponse>(
        `/weather/forecast?city_id=${cityId}&days=${days}`
      ),
    enabled: !!cityId,
  });
};