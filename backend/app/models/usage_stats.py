from datetime import date

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UsageStat(Base):
    __tablename__ = "usage_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    total_requests: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    unique_users: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    city_queries_json: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint("date", "platform", name="uq_usage_stats_date_platform"),
    )
