"""Main API router aggregating all v1 sub-routers."""

from fastapi import APIRouter

from app.api.v1 import cities, sources, users, weather

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(weather.router)
api_router.include_router(cities.router)
api_router.include_router(sources.router)
api_router.include_router(users.router)
