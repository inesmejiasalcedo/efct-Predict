"""Perfiles tipicos por hora (curvas base) que usa el modelo. Responsable: Harry.

Son curvas de referencia para restaurantes urbanos en Peru. El modelo las ajusta con los
datos externos reales (clima, trafico, macro) y con el aforo de cada sede.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo

    LIMA_TZ = ZoneInfo("America/Lima")
except Exception:  # Windows sin tzdata: Peru no tiene horario de verano
    LIMA_TZ = timezone(timedelta(hours=-5))


def to_local(dt_utc: datetime) -> datetime:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(LIMA_TZ)


def _bump(hour: float, center: float, width: float, height: float) -> float:
    return height * math.exp(-((hour - center) ** 2) / (2 * width ** 2))


def typical_congestion(hour: int, weekday: int) -> float:
    """Congestion vehicular tipica (0..1) segun hora local y dia (0 = lunes)."""
    value = 0.08 + _bump(hour, 8, 1.3, 0.40) + _bump(hour, 13.5, 1.5, 0.18) + _bump(hour, 19, 1.6, 0.48)
    if weekday == 5:      # sabado: manana mas tranquila, noche movida
        value = 0.08 + _bump(hour, 12, 2.5, 0.25) + _bump(hour, 20, 2.0, 0.35)
    elif weekday == 6:    # domingo
        value = 0.06 + _bump(hour, 13, 2.5, 0.22) + _bump(hour, 18, 2.0, 0.15)
    return round(min(max(value, 0.0), 0.95), 3)


def base_demand(hour: int, weekday: int) -> float:
    """Ocupacion tipica del salon como fraccion del aforo (0..1)."""
    lunch = _bump(hour, 13.3, 1.2, 0.68)
    dinner = _bump(hour, 20.2, 1.4, 0.62)
    if weekday in (4, 5):     # viernes y sabado: cenas fuertes
        dinner *= 1.30
    if weekday == 6:          # domingo: almuerzo familiar fuerte, noche floja
        lunch *= 1.30
        dinner *= 0.70
    if weekday == 0:          # lunes flojo
        lunch *= 0.85
        dinner *= 0.80
    return round(min(0.06 + lunch + dinner, 1.0), 3)


def is_peak(hour: int) -> bool:
    return 12 <= hour <= 14 or 19 <= hour <= 21
