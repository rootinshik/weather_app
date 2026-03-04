import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/apiClient";
import { CitySearchResult } from "../types/city";

export const useCitySearch = (query: string) => {
  return useQuery<CitySearchResult[]>({
    queryKey: ["citySearch", query],
    queryFn: () =>
      apiClient.get<CitySearchResult[]>(
        `/cities/search?q=${query}&limit=5`
      ),
    enabled: query.length > 1,
  });
};