"""Pydantic schemas for user data."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserIdentifyRequest(BaseModel):
    """Request body for POST /users/identify."""

    platform: str = Field(description="Client platform: 'web' or 'telegram'")
    external_id: str = Field(
        min_length=1,
        max_length=200,
        description="UUID cookie for web, chat_id for telegram",
    )


class UserPreferencesUpdate(BaseModel):
    """Request body for PATCH /users/{user_id}/preferences."""

    preferred_city_id: int | None = None
    settings_json: dict[str, Any] | None = None


class UserResponse(BaseModel):
    """User record as stored in the database."""

    id: int
    platform: str
    external_id: str
    preferred_city_id: int | None
    settings_json: dict[str, Any] | None
    created_at: datetime
    last_active_at: datetime

    model_config = ConfigDict(from_attributes=True)
