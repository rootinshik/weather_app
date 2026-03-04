import { useMutation } from "@tanstack/react-query";
import { apiClient } from "../api/apiClient";
import { CityResponse } from "../types/city";

export const useCreateCity = () => {
  return useMutation<CityResponse, Error, {
    name: string;
    country: string;
    lat: number;
    lon: number;
  }>({
    mutationFn: (cityData) =>
      apiClient.post<CityResponse>("/cities", cityData),
  });
};