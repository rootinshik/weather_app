export interface StatsRow {
  date: string;
  platform: string;
  total_requests: number;
  unique_users: number;
  city_queries_json: Record<string, unknown> | null;
}

export interface LogEntryResponse {
  id: number;
  user_id: number | null;
  platform: string;
  action: string;
  city_id: number | null;
  request_meta: Record<string, unknown> | null;
  created_at: string;
}

export interface LogsResponse {
  total: number;
  offset: number;
  limit: number;
  items: LogEntryResponse[];
}

export interface SourceUpdateRequest {
  is_enabled?: boolean;
  priority?: number;
}

export interface FetchNowResponse {
  triggered: boolean;
  cities_count: number;
}
