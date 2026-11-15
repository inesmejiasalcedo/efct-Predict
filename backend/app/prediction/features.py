"""Construccion de variables (features) por hora. Responsable: Harry.

Combina los datos limpios del pipeline (clima, pronostico, trafico, macro) con la
configuracion de la sede para obtener una fila por cada hora de las proximas 24 horas.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.prediction.profiles import is_peak, to_local, typical_congestion


@dataclass
class SiteContext:
    capacity: int
    open_hour: int
    close_hour: int
    avg_menu_price: float | None = None


@dataclass
class ExternalData:
    weather: dict | None = None
    forecast: list[dict] = field(default_factory=list)
    traffic: dict | None = None
    traffic_history: list[float] = field(default_factory=list)  # congestion de los ultimos 90 min
    macro: dict | None = None
    simulated_sources: list[str] = field(default_factory=list)


def rain_norm(rain_mm_h: float) -> float:
    """0 mm -> 0, 2 mm/h o mas -> 1 (lluvia fuerte para estandares peruanos)."""
    return min(max(rain_mm_h, 0.0) / 2.0, 1.0)


def traffic_volatility(history: list[float]) -> float:
    if len(history) < 3:
        return 0.0
    return round(max(history) - min(history), 3)


def project_congestion(current: float | None, now_local: datetime, target_local: datetime) -> float:
    """Proyecta la congestion a una hora futura usando el perfil tipico.

    Si ahora hay mas trafico de lo normal, ese exceso se va disipando con las horas.
    """
    typical_target = typical_congestion(target_local.hour, target_local.weekday())
    if current is None:
        return typical_target
    typical_now = max(typical_congestion(now_local.hour, now_local.weekday()), 0.05)
    k = min(max(current / typical_now, 0.6), 1.8)
    hours_ahead = max((target_local - now_local).total_seconds() / 3600, 0)
    k_h = 1 + (k - 1) * math.exp(-hours_ahead / 4)
    return round(min(typical_target * k_h, 0.95), 3)


def _forecast_at(forecast: list[dict], when_utc: datetime) -> dict | None:
    key = when_utc.strftime("%Y-%m-%dT%H:00:00Z")
    for row in forecast:
        if row.get("time") == key:
            return row
    # si no hay coincidencia exacta usamos la hora mas cercana (max 3h)
    best, best_gap = None, 3 * 3600 + 1
    for row in forecast:
        try:
            t = datetime.strptime(row["time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        gap = abs((t - when_utc).total_seconds())
        if gap < best_gap:
            best, best_gap = row, gap
    return best


def build_hourly_features(site: SiteContext, ext: ExternalData, now_utc: datetime | None = None, hours: int = 24) -> list[dict]:
    now_utc = (now_utc or datetime.now(timezone.utc)).replace(minute=0, second=0, microsecond=0)
    now_local = to_local(now_utc)
    current_cong = ext.traffic.get("congestion") if ext.traffic else None
    volatility = traffic_volatility(ext.traffic_history)
    rows = []
    for i in range(hours):
        t_utc = now_utc + timedelta(hours=i)
        t_local = to_local(t_utc)
        fc = _forecast_at(ext.forecast, t_utc) or {}
        if i == 0 and ext.weather:
            rain = ext.weather.get("rain_mm_h", 0.0)
            temp = ext.weather.get("temp_c", fc.get("temp_c", 20.0))
            pop = max(fc.get("pop", 0.0), 1.0 if rain > 0 else 0.0)
        else:
            rain = fc.get("rain_mm_h", 0.0)
            temp = fc.get("temp_c", 20.0)
            pop = fc.get("pop", 0.0)
        congestion = project_congestion(current_cong, now_local, t_local)
        congestion = min(congestion + 0.08 * rain_norm(rain), 0.95)  # la lluvia empeora el trafico
        rows.append(
            {
                "time": t_local.isoformat(timespec="minutes"),
                "hour": t_local.hour,
                "weekday": t_local.weekday(),
                "in_service": site.open_hour <= t_local.hour < site.close_hour,
                "peak": is_peak(t_local.hour),
                "rain_mm_h": round(rain, 2),
                "pop": round(pop, 2),
                "temp_c": round(temp, 1),
                "congestion": round(congestion, 3),
                "volatility": volatility if i < 2 else 0.0,
            }
        )
    return rows
