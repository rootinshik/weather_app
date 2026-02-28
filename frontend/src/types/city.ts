export interface CitySearchResult {
  name: string;
  local_name: string | null;
  country: string;
  lat: number;
  lon: number;
}

export interface CityCreate {
  name: string;
  local_name: string | null;
  country: string;
  lat: number;
  lon: number;
}

export interface CityResponse {
  id: number;
  name: string;
  local_name: string | null;
  country: string;
  lat: number;
  lon: number;
  created_at: string;
}
