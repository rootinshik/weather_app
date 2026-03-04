import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/apiClient";

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

export const useCurrentWeather = (cityId: number) => {
  return useQuery<CurrentWeatherResponse>({
    queryKey: ["Текущая погода", cityId],
    queryFn: () =>
      apiClient.get<CurrentWeatherResponse>(
        `/weather/current?city_id=${cityId}`
      ),
    enabled: !!cityId,
    retry: 1,
  });
};