"""Main API router aggregating all v1 sub-routers."""

from fastapi import APIRouter

from app.api.v1 import weather

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(weather.router)
