"""Generacion de predicciones para las proximas 24 horas. Responsable: Harry.

Entrada: features por hora (features.py) + datos macro.
Salida: serie horaria + resumen de cada riesgo con su peor ventana horaria.
"""
from __future__ import annotations

from app.prediction import risk as R
from app.prediction.actions import actions_for
from app.prediction.features import SiteContext


def _windows(rows: list[dict], key: str, threshold: int) -> dict | None:
    """Ventana contigua alrededor de la peor hora donde el riesgo supera el umbral."""
    if not rows:
        return None
    worst_i = max(range(len(rows)), key=lambda i: rows[i][key])
    if rows[worst_i][key] < threshold:
        return None

    def consecutive(a: dict, b: dict) -> bool:
        return (a["hour"] + 1) % 24 == b["hour"]

    lo = hi = worst_i
    while lo > 0 and rows[lo - 1][key] >= threshold and consecutive(rows[lo - 1], rows[lo]):
        lo -= 1
    while hi < len(rows) - 1 and rows[hi + 1][key] >= threshold and consecutive(rows[hi], rows[hi + 1]):
        hi += 1
    return {"from": rows[lo]["hour"], "to": (rows[hi]["hour"] + 1) % 24, "start_time": rows[lo]["time"]}


def predict(site: SiteContext, feature_rows: list[dict], macro: dict | None) -> dict:
    hourly = []
    for f in feature_rows:
        d_score, d_factors = R.delivery_score(f)
        a_score, a_factors = R.arrival_score(f)
        m_score, m_dir, m_detail = R.demand_score(f)
        occ = m_detail["occupancy"]
        hourly.append(
            {
                **f,
                "delivery": d_score,
                "arrival": a_score,
                "demand": m_score if f["in_service"] else 0,
                "demand_direction": m_dir if f["in_service"] else "closed",
                "occupancy": occ if f["in_service"] else 0.0,
                "expected_guests": round(occ * site.capacity) if f["in_service"] else 0,
                "normal_guests": round(m_detail["base"] * site.capacity) if f["in_service"] else 0,
                "_delivery_factors": d_factors,
                "_arrival_factors": a_factors,
                "_demand_detail": m_detail,
            }
        )

    service_rows = [h for h in hourly if h["in_service"]] or hourly

    # --- Afluencia: peor hora de servicio
    worst_d = max(service_rows, key=lambda h: h["demand"])
    demand = {
        "type": "demand",
        "score": worst_d["demand"],
        "direction": worst_d["demand_direction"],
        "hour": worst_d["hour"],
        "time": worst_d["time"],
        "window": _windows(service_rows, "demand", 40),
        "factors": worst_d["_demand_detail"]["factors"],
        "detail": {k: v for k, v in worst_d["_demand_detail"].items() if k != "factors"},
    }

    # --- Delivery: peor hora de servicio
    worst_del = max(service_rows, key=lambda h: h["delivery"])
    delivery = {
        "type": "delivery",
        "score": worst_del["delivery"],
        "hour": worst_del["hour"],
        "time": worst_del["time"],
        "window": _windows(service_rows, "delivery", 40),
        "factors": worst_del["_delivery_factors"],
    }

    # --- Llegada: una hora antes de la apertura mas cercana (o la hora actual si ya abrio)
    arrival_hour = (site.open_hour - 1) % 24
    arr_row = next((h for h in hourly if h["hour"] == arrival_hour), hourly[0])
    arrival = {
        "type": "arrival",
        "score": arr_row["arrival"],
        "hour": arr_row["hour"],
        "time": arr_row["time"],
        "window": None,
        "factors": arr_row["_arrival_factors"],
    }

    # --- Costos: indicadores nacionales
    c_score, c_factors = R.cost_score(macro)
    cost = {
        "type": "cost",
        "score": c_score,
        "hour": None,
        "time": None,
        "window": None,
        "factors": c_factors,
        "detail": {
            "fx_last": (macro or {}).get("fx_last"),
            "fx_change_30d_pct": (macro or {}).get("fx_change_30d_pct"),
            "food_inflation_12m_pct": (macro or {}).get("food_inflation_12m_pct"),
        },
    }

    risks = [demand, delivery, arrival, cost]
    for r in risks:
        r["level"] = R.level_for(r["score"])
        r["actions"] = actions_for(r)

    scores = {r["type"]: r["score"] for r in risks}
    overall = R.overall_score(scores)
    main = max(risks, key=lambda r: r["score"])

    clean_hourly = [{k: v for k, v in h.items() if not k.startswith("_")} for h in hourly]
    actions = sorted((a for r in risks for a in r["actions"]), key=lambda a: a["priority"])

    return {
        "overall": {"score": overall, "level": R.level_for(overall), "main_risk": main["type"]},
        "risks": risks,
        "hourly": clean_hourly,
        "top_actions": [a for a in actions if not a["code"].endswith("_normal")][:4],
    }
