"""Stats service: aggregate request_logs into usage_stats and query both tables."""

import logging
from datetime import date, datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request_log import RequestLog
from app.models.usage_stats import UsageStat

logger = logging.getLogger(__name__)


class StatsService:
    """Service for usage statistics and request log queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_stats(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
        platform: str | None = None,
    ) -> list[UsageStat]:
        """Query usage_stats with optional filters.

        Args:
            from_date: Inclusive start date filter
            to_date: Inclusive end date filter
            platform: Filter by platform ('web' or 'telegram')

        Returns:
            List of UsageStat rows ordered by date descending
        """
        query = select(UsageStat).order_by(UsageStat.date.desc())

        if from_date:
            query = query.where(UsageStat.date >= from_date)
        if to_date:
            query = query.where(UsageStat.date <= to_date)
        if platform:
            query = query.where(UsageStat.platform == platform)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        platform: str | None = None,
        action: str | None = None,
    ) -> tuple[int, list[RequestLog]]:
        """Query request_logs with pagination and optional filters.

        Args:
            limit: Maximum rows to return
            offset: Number of rows to skip
            platform: Filter by platform
            action: Partial match on action field

        Returns:
            Tuple of (total_count, rows)
        """
        base_filter = []
        if platform:
            base_filter.append(RequestLog.platform == platform)
        if action:
            base_filter.append(RequestLog.action.contains(action))

        count_query = select(func.count(RequestLog.id))
        rows_query = (
            select(RequestLog)
            .order_by(RequestLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        for condition in base_filter:
            count_query = count_query.where(condition)
            rows_query = rows_query.where(condition)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        rows_result = await self.db.execute(rows_query)
        return total, list(rows_result.scalars().all())

    async def aggregate_today(self) -> None:
        """Aggregate today's request_logs into usage_stats (upsert per platform)."""
        today = date.today()
        day_start = datetime.combine(today, time.min).replace(tzinfo=timezone.utc)

        platform_query = (
            select(
                RequestLog.platform,
                func.count(RequestLog.id).label("total"),
                func.count(func.distinct(RequestLog.user_id)).label("unique_users"),
            )
            .where(RequestLog.created_at >= day_start)
            .group_by(RequestLog.platform)
        )

        result = await self.db.execute(platform_query)
        rows = result.all()

        for platform, total, unique_users in rows:
            existing_result = await self.db.execute(
                select(UsageStat).where(
                    UsageStat.date == today,
                    UsageStat.platform == platform,
                )
            )
            stat = existing_result.scalar_one_or_none()

            if stat:
                stat.total_requests = total
                stat.unique_users = unique_users
            else:
                self.db.add(
                    UsageStat(
                        date=today,
                        platform=platform,
                        total_requests=total,
                        unique_users=unique_users,
                    )
                )

        await self.db.commit()
        logger.info("Aggregated today's stats: %d platforms", len(rows))
