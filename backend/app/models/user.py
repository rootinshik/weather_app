from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    preferred_city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"))
    settings_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    last_active_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_users_platform_external_id"),
    )
