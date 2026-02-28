export interface AggregatedWeather {
  temperature: number | null;
  feels_like: number | null;
  wind_speed: number | null;
  wind_direction: number | null;
  humidity: number | null;
  pressure: number | null;
  precipitation_type: string | null;
  precipitation_amount: number | null;
  cloudiness: number | null;
  description: string | null;
  icon_code: string | null;
}

export interface AggregatedWeatherResponse {
  city_id: number;
  fetched_at: string;
  weather: AggregatedWeather;
}

export interface ForecastPoint {
  forecast_dt: string;
  weather: AggregatedWeather;
}

export interface ForecastResponse {
  city_id: number;
  days: number;
  forecasts: ForecastPoint[];
}

export interface SourceWeatherData {
  source_name: string;
  priority: number;
  fetched_at: string;
  weather: AggregatedWeather;
}

export interface SourceWeatherResponse {
  city_id: number;
  sources: Record<string, SourceWeatherData>;
}

export interface ChartPoint {
  hour: string;
  temperature: number | null;
  feels_like: number | null;
  precipitation_amount: number | null;
  wind_speed: number | null;
  humidity: number | null;
}

export interface DailyChartPoint {
  date: string;
  temp_min: number;
  temp_max: number;
  temp_avg: number;
}
