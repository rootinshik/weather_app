"""Users API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.user import UserIdentifyRequest, UserPreferencesUpdate, UserResponse
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def _get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


@router.post("/identify", response_model=UserResponse)
async def identify_user(
    body: UserIdentifyRequest,
    service: UserService = Depends(_get_user_service),
) -> UserResponse:
    """Identify a user by platform + external_id.

    Creates a new user on first call; returns existing user on subsequent calls.
    Also updates last_active_at for returning users.
    """
    user = await service.identify(body.platform, body.external_id)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(_get_user_service),
) -> UserResponse:
    """Get a user by their database ID."""
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/preferences", response_model=UserResponse)
async def update_preferences(
    user_id: int,
    body: UserPreferencesUpdate,
    service: UserService = Depends(_get_user_service),
) -> UserResponse:
    """Update user preferences (preferred city, settings)."""
    user = await service.update_preferences(user_id, body)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return UserResponse.model_validate(user)
