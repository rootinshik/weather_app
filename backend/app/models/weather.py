from datetime import datetime

from sqlalchemy import Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("weather_sources.id"), nullable=False)
    record_type: Mapped[str] = mapped_column(String(10), nullable=False)
    forecast_dt: Mapped[datetime | None] = mapped_column()
    temperature: Mapped[float | None] = mapped_column(Float)
    feels_like: Mapped[float | None] = mapped_column(Float)
    wind_speed: Mapped[float | None] = mapped_column(Float)
    wind_direction: Mapped[int | None] = mapped_column(Integer)
    humidity: Mapped[int | None] = mapped_column(Integer)
    pressure: Mapped[float | None] = mapped_column(Float)
    precipitation_type: Mapped[str | None] = mapped_column(String(20))
    precipitation_amount: Mapped[float | None] = mapped_column(Float)
    cloudiness: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(String(500))
    icon_code: Mapped[str | None] = mapped_column(String(50))
    fetched_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())

    __table_args__ = (
        Index("ix_weather_records_city_type", "city_id", "record_type"),
        Index("ix_weather_records_city_source_dt", "city_id", "source_id", "forecast_dt"),
    )
