import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/apiClient";

export interface HourlyPoint {
  hour: string;
  temperature: number;
  feels_like: number;
  precipitation_amount?: number | null;
  wind_speed: number;
  humidity: number;
}

export const useHourlyChart = (cityId: number) => {
  return useQuery<HourlyPoint[]>({
    queryKey: ["hourlyChart", cityId],
    queryFn: () =>
      apiClient.get<HourlyPoint[]>(
        `/weather/chart/hourly?city_id=${cityId}`
      ),
    enabled: !!cityId,
  });
};