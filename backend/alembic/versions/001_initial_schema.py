"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("local_name", sa.String(200), nullable=True),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cities_name", "cities", ["name"])

    op.create_table(
        "weather_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("config_file", sa.String(200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "weather_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("record_type", sa.String(10), nullable=False),
        sa.Column("forecast_dt", sa.DateTime(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("feels_like", sa.Float(), nullable=True),
        sa.Column("wind_speed", sa.Float(), nullable=True),
        sa.Column("wind_direction", sa.Integer(), nullable=True),
        sa.Column("humidity", sa.Integer(), nullable=True),
        sa.Column("pressure", sa.Float(), nullable=True),
        sa.Column("precipitation_type", sa.String(20), nullable=True),
        sa.Column("precipitation_amount", sa.Float(), nullable=True),
        sa.Column("cloudiness", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("icon_code", sa.String(50), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["weather_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_weather_records_city_type", "weather_records", ["city_id", "record_type"]
    )
    op.create_index(
        "ix_weather_records_city_source_dt",
        "weather_records",
        ["city_id", "source_id", "forecast_dt"],
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("preferred_city_id", sa.Integer(), nullable=True),
        sa.Column("settings_json", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["preferred_city_id"], ["cities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("platform", "external_id", name="uq_users_platform_external_id"),
    )

    op.create_table(
        "request_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=True),
        sa.Column("request_meta", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_request_logs_created", "request_logs", ["created_at"])

    op.create_table(
        "usage_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("total_requests", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unique_users", sa.Integer(), server_default="0", nullable=False),
        sa.Column("city_queries_json", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date", "platform", name="uq_usage_stats_date_platform"),
    )


def downgrade() -> None:
    op.drop_table("usage_stats")
    op.drop_index("ix_request_logs_created", table_name="request_logs")
    op.drop_table("request_logs")
    op.drop_table("users")
    op.drop_index("ix_weather_records_city_source_dt", table_name="weather_records")
    op.drop_index("ix_weather_records_city_type", table_name="weather_records")
    op.drop_table("weather_records")
    op.drop_table("weather_sources")
    op.drop_index("ix_cities_name", table_name="cities")
    op.drop_table("cities")
