"""Snapshots de datos externos ya limpios. Responsable: Harry."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base, utcnow

SOURCE_WEATHER = "weather"      # clima actual (OpenWeather)
SOURCE_FORECAST = "forecast"    # pronostico por hora (OpenWeather)
SOURCE_TRAFFIC = "traffic"      # flujo vehicular (TomTom)
SOURCE_MACRO = "macro"          # tipo de cambio e inflacion de alimentos (BCRP)

ALL_SOURCES = [SOURCE_WEATHER, SOURCE_FORECAST, SOURCE_TRAFFIC, SOURCE_MACRO]


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sites.id", ondelete="CASCADE"), nullable=True, index=True
    )  # None para datos nacionales (BCRP)
    source: Mapped[str] = mapped_column(String(20), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
