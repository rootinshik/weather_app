import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/apiClient";

export interface RecommendationData {
  summary: string;
  advice: string[];
  risk_level?: string;
}

export interface RecommendationResponse {
  city_id: number;
  recommendation: RecommendationData;
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