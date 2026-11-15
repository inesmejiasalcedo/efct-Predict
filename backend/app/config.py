"""Configuracion central. Todo se lee de variables de entorno (archivo .env).

Ningun secreto vive en el codigo: ver .env.example.
"""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # carpeta backend/
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "si", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'efct.db'}")
    )
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", ""))
    token_minutes: int = field(default_factory=lambda: _int("TOKEN_MINUTES", 480))

    admin_email: str = field(default_factory=lambda: os.getenv("ADMIN_EMAIL", ""))
    admin_password: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", ""))

    tomtom_api_key: str = field(default_factory=lambda: os.getenv("TOMTOM_API_KEY", ""))
    openweather_api_key: str = field(default_factory=lambda: os.getenv("OPENWEATHER_API_KEY", ""))

    scheduler_enabled: bool = field(default_factory=lambda: _bool("SCHEDULER_ENABLED", True))
    weather_refresh_min: int = field(default_factory=lambda: _int("WEATHER_REFRESH_MINUTES", 30))
    traffic_refresh_min: int = field(default_factory=lambda: _int("TRAFFIC_REFRESH_MINUTES", 15))
    macro_refresh_min: int = field(default_factory=lambda: _int("MACRO_REFRESH_MINUTES", 720))
    allow_simulated_data: bool = field(default_factory=lambda: _bool("ALLOW_SIMULATED_DATA", True))

    cors_origins: list[str] = field(
        default_factory=lambda: [
            o.strip()
            for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
            if o.strip()
        ]
    )
    timezone: str = field(default_factory=lambda: os.getenv("APP_TIMEZONE", "America/Lima"))

    def __post_init__(self) -> None:
        if not self.secret_key:
            # Sin SECRET_KEY generamos una temporal: las sesiones se pierden al reiniciar.
            self.secret_key = secrets.token_urlsafe(48)
            self.secret_key_is_temporary = True
        else:
            self.secret_key_is_temporary = False

    @property
    def has_tomtom(self) -> bool:
        return bool(self.tomtom_api_key)

    @property
    def has_openweather(self) -> bool:
        return bool(self.openweather_api_key)


settings = Settings()
