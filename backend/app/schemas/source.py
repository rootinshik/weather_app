"""Pydantic schemas for weather source data."""

from pydantic import BaseModel, ConfigDict


class SourceResponse(BaseModel):
    """Weather data source as stored in the database."""

    id: int
    slug: str
    display_name: str
    source_type: str
    priority: int
    is_enabled: bool

    model_config = ConfigDict(from_attributes=True)
