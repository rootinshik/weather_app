export interface UserIdentifyRequest {
  platform: string;
  external_id: string;
}

export interface UserPreferencesUpdate {
  preferred_city_id?: number | null;
  settings_json?: Record<string, unknown> | null;
}

export interface UserResponse {
  id: number;
  platform: string;
  external_id: string;
  preferred_city_id: number | null;
  settings_json: Record<string, unknown> | null;
  created_at: string;
  last_active_at: string;
}
