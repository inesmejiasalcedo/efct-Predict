"""Personalizacion del negocio: restaurante, sedes y menu. Responsable: Matias.

Solo datos publicos del negocio (nombre, ubicacion, aforo, precios). Nada confidencial.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.db import Base, utcnow


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    sites: Mapped[list["Site"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")
    menu_items: Mapped[list["MenuItem"]] = relationship(back_populates="restaurant", cascade="all, delete-orphan")


class Site(Base):
    """Sede del restaurante. Su ubicacion define que datos externos se consultan."""

    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    capacity: Mapped[int] = mapped_column(Integer)  # aforo (personas)
    open_hour: Mapped[int] = mapped_column(Integer, default=12)
    close_hour: Mapped[int] = mapped_column(Integer, default=23)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    restaurant: Mapped[Restaurant] = relationship(back_populates="sites")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    price: Mapped[float] = mapped_column(Float)  # soles (PEN)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    restaurant: Mapped[Restaurant] = relationship(back_populates="menu_items")
