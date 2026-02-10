from datetime import datetime

from sqlalchemy import Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    local_name: Mapped[str | None] = mapped_column(String(200))
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    lat: Mapped[float] = mapped_column(nullable=False)
    lon: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())

    __table_args__ = (
        Index("ix_cities_name", "name"),
    )
