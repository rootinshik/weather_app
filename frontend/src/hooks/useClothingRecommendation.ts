import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/apiClient";

export interface RecommendationResponse {
  city_id: number;
  category: string;
  description: string;
  items: string[];
}

export const useClothingRecommendation = (cityId: number) => {
  return useQuery<RecommendationResponse>({
    queryKey: ["Рекомендация", cityId],
    queryFn: () =>
      apiClient.get<RecommendationResponse>(
        `/recommendations/clothing?city_id=${cityId}`
      ),
    enabled: !!cityId,
  });
};