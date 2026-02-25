"""User service: create, identify, and update users."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserPreferencesUpdate

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def identify(self, platform: str, external_id: str) -> User:
        """Get existing user or create a new one.

        Called on every client session start. Updates last_active_at
        for returning users.

        Args:
            platform: Client platform ('web' or 'telegram')
            external_id: UUID cookie (web) or chat_id (telegram)

        Returns:
            User ORM instance (existing or newly created)
        """
        result = await self.db.execute(
            select(User).where(
                User.platform == platform,
                User.external_id == external_id,
            )
        )
        user = result.scalar_one_or_none()

        if user:
            user.last_active_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(user)
            return user

        user = User(
            platform=platform,
            external_id=external_id,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        """Get a user by database ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def update_preferences(
        self, user_id: int, update: UserPreferencesUpdate
    ) -> User | None:
        """Update user preferences (preferred city and/or settings).

        Args:
            user_id: Database ID of the user
            update: Fields to update (only non-None values are applied)

        Returns:
            Updated user, or None if user not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None

        if update.preferred_city_id is not None:
            user.preferred_city_id = update.preferred_city_id
        if update.settings_json is not None:
            user.settings_json = update.settings_json

        await self.db.commit()
        await self.db.refresh(user)
        return user
