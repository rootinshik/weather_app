from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WeatherSource(Base):
    __tablename__ = "weather_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    config_file: Mapped[str] = mapped_column(String(200), nullable=False)
