import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/apiClient";

export interface DailyPoint {
  date: string;
  temp_min: number;
  temp_max: number;
  temp_avg: number;
}

export const useDailyChart = (cityId: number) => {
  return useQuery<DailyPoint[]>({
    queryKey: ["dailyChart", cityId],
    queryFn: () =>
      apiClient.get<DailyPoint[]>(
        `/weather/chart/daily?city_id=${cityId}&days=7`
      ),
    enabled: !!cityId,
  });
};