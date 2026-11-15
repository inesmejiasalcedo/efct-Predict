"""Datos simulados para cuando NO hay API keys (modo demo). Responsable: Harry.

Siempre se guardan con is_simulated=True y la interfaz lo muestra claramente.
Son deterministas (misma sede + misma hora = mismo valor) para que las demos sean estables.
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta, timezone

from app.prediction.profiles import to_local, typical_congestion


def _rng(*parts) -> random.Random:
    return random.Random("|".join(str(p) for p in parts))


def _climate(lat: float, lon: float, month: int) -> dict:
    """Clima aproximado por zona del Peru y mes."""
    summer = month in (12, 1, 2, 3, 4)
    rainy_andes = month in (11, 12, 1, 2, 3)
    if lon > -73.5 and lat < -12.5 and lat > -15:          # Cusco / sierra sur
        return {"temp": 14 if rainy_andes else 11, "amp": 6, "rain_p": 0.45 if rainy_andes else 0.08, "rain_mm": 1.6}
    if lon > -72.5 and lat < -15:                          # Arequipa
        return {"temp": 19, "amp": 6, "rain_p": 0.25 if month in (1, 2, 3) else 0.03, "rain_mm": 1.0}
    return {                                               # costa (Lima, Trujillo, Callao)
        "temp": 24 if summer else 18,
        "amp": 4 if summer else 2,
        "rain_p": 0.04 if summer else 0.22,                # garua en invierno
        "rain_mm": 0.6 if summer else 0.15,
    }


def _hour_weather(lat: float, lon: float, when_utc: datetime) -> dict:
    local = to_local(when_utc)
    c = _climate(lat, lon, local.month)
    r = _rng(round(lat, 2), round(lon, 2), local.strftime("%Y%m%d%H"))
    day = _rng(round(lat, 2), round(lon, 2), local.strftime("%Y%m%d"))
    rainy_day = day.random() < c["rain_p"] * 1.6
    temp = c["temp"] + c["amp"] * math.sin((local.hour - 9) / 24 * 2 * math.pi) + r.uniform(-0.8, 0.8)
    pop = min(1.0, (0.55 if rainy_day else 0.05) + r.uniform(0, 0.25))
    raining = rainy_day and r.random() < 0.55
    rain = round(c["rain_mm"] * r.uniform(0.4, 1.8), 2) if raining else 0.0
    return {
        "temp_c": round(temp, 1),
        "pop": round(pop, 2),
        "rain_mm_h": rain,
        "condition": "Rain" if rain > 0.3 else ("Drizzle" if rain > 0 else ("Clouds" if pop > 0.4 else "Clear")),
    }


def simulated_current_weather(lat: float, lon: float, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    h = _hour_weather(lat, lon, now)
    return {
        "temp_c": h["temp_c"],
        "feels_like_c": h["temp_c"],
        "humidity": 78,
        "rain_mm_h": h["rain_mm_h"],
        "wind_ms": 3.2,
        "condition": h["condition"],
        "description": "simulado",
        "observed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def simulated_forecast(lat: float, lon: float, hours: int = 36, now: datetime | None = None) -> list[dict]:
    now = (now or datetime.now(timezone.utc)).replace(minute=0, second=0, microsecond=0)
    out = []
    for i in range(hours):
        t = now + timedelta(hours=i)
        h = _hour_weather(lat, lon, t)
        out.append({"time": t.strftime("%Y-%m-%dT%H:%M:%SZ"), **h})
    return out


def simulated_traffic(lat: float, lon: float, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    local = to_local(now)
    r = _rng(round(lat, 2), round(lon, 2), local.strftime("%Y%m%d%H%M")[:-1])
    congestion = min(0.95, max(0.0, typical_congestion(local.hour, local.weekday()) + r.uniform(-0.08, 0.08)))
    free = 50.0
    return {
        "current_speed_kmh": round(free * (1 - congestion), 1),
        "free_flow_speed_kmh": free,
        "congestion": round(congestion, 3),
        "travel_time_ratio": round(1 / max(1 - congestion, 0.1), 2),
        "confidence": 0.8,
        "road_closure": False,
    }


def simulated_macro(today: datetime | None = None) -> dict:
    today = today or datetime.now(timezone.utc)
    fx = []
    for i in range(45, -1, -1):
        d = today - timedelta(days=i)
        if d.weekday() >= 5:
            continue
        r = _rng("fx", d.strftime("%Y%m%d"))
        fx.append({"period": d.strftime("%Y-%m-%d"), "value": round(3.72 + 0.03 * math.sin(i / 9) + r.uniform(-0.01, 0.01), 3)})
    food = []
    for i in range(12, -1, -1):
        y, m = today.year, today.month - i
        while m <= 0:
            m += 12
            y -= 1
        food.append({"period": f"{y:04d}-{m:02d}", "value": round(2.4 + 0.4 * math.sin(i / 3), 2)})
    from app.ingestion.cleaning import summarize_macro

    return summarize_macro(fx, food)
