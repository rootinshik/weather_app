"""Pydantic schemas for admin API."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.source import SourceResponse  # re-exported for admin use


class AdminAuthResponse(BaseModel):
    authenticated: bool


class StatsRow(BaseModel):
    """One row of usage_stats (per day per platform)."""

    date: date
    platform: str
    total_requests: int
    unique_users: int
    city_queries_json: dict[str, Any] | None

    model_config = ConfigDict(from_attributes=True)


class LogEntryResponse(BaseModel):
    """One row from request_logs."""

    id: int
    user_id: int | None
    platform: str
    action: str
    city_id: int | None
    request_meta: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LogsResponse(BaseModel):
    """Paginated list of request logs."""

    total: int
    offset: int
    limit: int
    items: list[LogEntryResponse]


class SourceUpdateRequest(BaseModel):
    """Body for PATCH /admin/sources/{slug}."""

    is_enabled: bool | None = None
    priority: int | None = Field(None, ge=1)


class FetchNowResponse(BaseModel):
    """Response for POST /admin/fetch-now."""

    triggered: bool
    cities_count: int
