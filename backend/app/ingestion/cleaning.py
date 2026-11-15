"""Filtrado y limpieza de datos crudos de las APIs. Responsable: Harry.

Reglas generales:
  1. Validar que vengan los campos minimos (si no, se rechaza el dato).
  2. Recortar valores fuera de rango fisico (clip) en vez de confiar ciegamente.
  3. Rellenar faltantes con valores neutros documentados (ej. lluvia ausente = 0 mm).
  4. Normalizar unidades: grados C, mm/h, km/h, fechas en UTC ISO-8601.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


class CleaningError(ValueError):
    """El dato crudo no tiene lo minimo para ser usado."""


def clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _num(value, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------ Clima

def clean_current_weather(raw: dict) -> dict:
    main = raw.get("main") or {}
    temp = _num(main.get("temp"))
    if temp is None:
        raise CleaningError("weather_missing_temp")
    weather = (raw.get("weather") or [{}])[0]
    rain = raw.get("rain") or {}
    rain_mm_h = _num(rain.get("1h"), None)
    if rain_mm_h is None:
        rain_mm_h = (_num(rain.get("3h"), 0.0) or 0.0) / 3.0
    return {
        "temp_c": round(clip(temp, -30, 55), 1),
        "feels_like_c": round(clip(_num(main.get("feels_like"), temp), -40, 60), 1),
        "humidity": int(clip(_num(main.get("humidity"), 70), 0, 100)),
        "rain_mm_h": round(clip(rain_mm_h, 0, 100), 2),
        "wind_ms": round(clip(_num((raw.get("wind") or {}).get("speed"), 0), 0, 60), 1),
        "condition": str(weather.get("main") or "Clear"),
        "description": str(weather.get("description") or ""),
        "observed_at": _iso(_num(raw.get("dt"), datetime.now(timezone.utc).timestamp())),
    }


def clean_forecast(raw: dict, hours: int = 36) -> list[dict]:
    """Convierte bloques de 3 horas en una serie por hora (cada bloque cubre 3 horas)."""
    blocks = raw.get("list") or []
    if not blocks:
        raise CleaningError("forecast_empty")
    seen: set[int] = set()
    hourly: list[dict] = []
    for block in sorted(blocks, key=lambda b: _num(b.get("dt"), 0)):
        ts = _num(block.get("dt"))
        main = block.get("main") or {}
        temp = _num(main.get("temp"))
        if ts is None or temp is None:
            continue  # bloque incompleto: se descarta
        rain_3h = _num((block.get("rain") or {}).get("3h"), 0.0) or 0.0
        pop = clip(_num(block.get("pop"), 0.0) or 0.0, 0, 1)
        condition = str(((block.get("weather") or [{}])[0]).get("main") or "Clear")
        for offset in range(3):
            hour_ts = int(ts) + offset * 3600
            if hour_ts in seen:
                continue  # elimina duplicados
            seen.add(hour_ts)
            hourly.append(
                {
                    "time": _iso(hour_ts),
                    "temp_c": round(clip(temp, -30, 55), 1),
                    "pop": round(pop, 2),
                    "rain_mm_h": round(clip(rain_3h / 3.0, 0, 100), 2),
                    "condition": condition,
                }
            )
    if not hourly:
        raise CleaningError("forecast_empty")
    return hourly[:hours]


# ------------------------------------------------------------------ Trafico

def clean_traffic(raw: dict) -> dict:
    flow = raw.get("flowSegmentData") or {}
    current = _num(flow.get("currentSpeed"))
    free = _num(flow.get("freeFlowSpeed"))
    if current is None or free is None or free <= 0:
        raise CleaningError("traffic_missing_speeds")
    current = clip(current, 0, 200)
    ratio = clip(current / free, 0, 1.0)  # >1 se considera flujo libre
    cur_tt = _num(flow.get("currentTravelTime"))
    free_tt = _num(flow.get("freeFlowTravelTime"))
    tt_ratio = round(clip(cur_tt / free_tt, 1, 10), 2) if cur_tt and free_tt else round(1 / max(ratio, 0.1), 2)
    return {
        "current_speed_kmh": round(current, 1),
        "free_flow_speed_kmh": round(free, 1),
        "congestion": round(1 - ratio, 3),  # 0 = libre, 1 = detenido
        "travel_time_ratio": tt_ratio,
        "confidence": round(clip(_num(flow.get("confidence"), 1.0), 0, 1), 2),
        "road_closure": bool(flow.get("roadClosure", False)),
    }


# ------------------------------------------------------------------ BCRP

_MONTHS_ES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12,
}


def parse_bcrp_period(name: str) -> str:
    """'02.Ene.25' -> '2025-01-02'   'Ene.2025' -> '2025-01'."""
    parts = [p for p in name.strip().replace("-", ".").split(".") if p]
    if len(parts) == 3:
        day, mon, year = parts
        year_i = int(year) + (2000 if len(year) == 2 else 0)
        return f"{year_i:04d}-{_MONTHS_ES[mon[:3].lower()]:02d}-{int(day):02d}"
    if len(parts) == 2:
        mon, year = parts
        year_i = int(year) + (2000 if len(year) == 2 else 0)
        return f"{year_i:04d}-{_MONTHS_ES[mon[:3].lower()]:02d}"
    raise CleaningError(f"bcrp_bad_period:{name}")


def clean_bcrp_series(raw: dict) -> list[dict]:
    points = []
    for period in raw.get("periods") or []:
        values = period.get("values") or []
        value = _num(str(values[0]).replace(",", ".") if values else None)
        if value is None:
            continue  # 'n.d.' u otros textos: se descartan
        try:
            points.append({"period": parse_bcrp_period(str(period.get("name", ""))), "value": value})
        except (CleaningError, KeyError, ValueError):
            continue
    points.sort(key=lambda p: p["period"])
    # dedupe por periodo (se queda el ultimo)
    dedup = {p["period"]: p for p in points}
    result = list(dedup.values())
    if not result:
        raise CleaningError("bcrp_empty")
    return result


def summarize_macro(fx_points: list[dict], food_points: list[dict]) -> dict:
    """Resume las series en indicadores que usa el modelo."""
    fx_last = fx_points[-1]["value"] if fx_points else None
    fx_change = None
    if fx_points and len(fx_points) >= 2:
        last_date = datetime.strptime(fx_points[-1]["period"], "%Y-%m-%d")
        target = last_date - timedelta(days=30)
        base = next((p for p in reversed(fx_points) if datetime.strptime(p["period"], "%Y-%m-%d") <= target), fx_points[0])
        if base["value"]:
            fx_change = round((fx_last - base["value"]) / base["value"] * 100, 2)
    return {
        "fx_last": fx_last,
        "fx_change_30d_pct": fx_change if fx_change is not None else 0.0,
        "food_inflation_12m_pct": food_points[-1]["value"] if food_points else None,
        "fx_series": fx_points[-45:],
        "food_series": food_points[-13:],
    }
