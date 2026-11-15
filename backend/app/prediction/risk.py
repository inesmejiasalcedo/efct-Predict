"""Calculo de riesgos. Responsable: Harry (modelo) y Diana (explicacion en detalle).

Cuatro riesgos, todos en escala 0-100:
  demand    Afluencia de clientes: cuanto se desvia la demanda esperada de lo normal.
  delivery  Retrasos en entregas a domicilio: trafico + lluvia + hora punta.
  arrival   Llegada del personal y proveedores a la hora de apertura.
  cost      Presion de costos de insumos: tipo de cambio e inflacion de alimentos.

Los riesgos delivery, arrival y cost usan un modelo logistico:
    score = 100 / (1 + e^-(bias + suma(peso_i * x_i)))
Los pesos viven en weights.json y se calibran con datos historicos (scripts/calibrate.py).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from app.prediction.features import rain_norm
from app.prediction.profiles import base_demand

WEIGHTS_PATH = Path(__file__).with_name("weights.json")
RISK_TYPES = ["demand", "delivery", "arrival", "cost"]


def load_weights(path: Path = WEIGHTS_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


WEIGHTS = load_weights()


def logistic(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


def level_for(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _logistic_score(weights: dict, inputs: dict[str, float]) -> tuple[int, list[dict]]:
    z = weights.get("bias", 0.0)
    contributions = []
    for name, x in inputs.items():
        w = weights.get(name, 0.0)
        z += w * x
        contributions.append({"factor": name, "value": round(x, 3), "weight": w, "impact": round(w * x, 3)})
    total_positive = sum(max(c["impact"], 0) for c in contributions) or 1.0
    for c in contributions:
        c["share_pct"] = round(max(c["impact"], 0) / total_positive * 100)
    contributions.sort(key=lambda c: c["impact"], reverse=True)
    return round(100 * logistic(z)), contributions


# ---------------------------------------------------------------- Delivery

def delivery_inputs(row: dict) -> dict[str, float]:
    return {
        "congestion": row["congestion"],
        "rain": rain_norm(row["rain_mm_h"]),
        "peak": 1.0 if row["peak"] else 0.0,
        "volatility": min(row.get("volatility", 0.0) / 0.2, 1.0),
        "pop": row["pop"],
    }


def delivery_probability(row: dict, weights: dict | None = None) -> tuple[int, list[dict]]:
    """Probabilidad (0-100) de que haya retrasos de mas de 15 min en las entregas."""
    return _logistic_score((weights or WEIGHTS)["delivery"], delivery_inputs(row))


def rescale_to_threshold(prob: float, threshold: float) -> int:
    """Lleva la probabilidad a la escala de la interfaz: el umbral calibrado queda en 50.

    Asi "50 o mas" siempre significa "el modelo espera un incidente", sin importar el umbral.
    """
    threshold = min(max(threshold, 1), 99)
    if prob < threshold:
        return round(50 * prob / threshold)
    return round(50 + 50 * (prob - threshold) / (100 - threshold))


def delivery_score(row: dict, weights: dict | None = None) -> tuple[int, list[dict]]:
    w = weights or WEIGHTS
    prob, factors = delivery_probability(row, w)
    return rescale_to_threshold(prob, w.get("threshold", 50)), factors


# ---------------------------------------------------------------- Arrival

def arrival_inputs(row: dict) -> dict[str, float]:
    weekday_rush = 1.0 if row["weekday"] < 5 and (7 <= row["hour"] <= 9 or 17 <= row["hour"] <= 20) else 0.0
    return {"congestion": row["congestion"], "rain": rain_norm(row["rain_mm_h"]), "weekday_rush": weekday_rush}


def arrival_score(row: dict, weights: dict | None = None) -> tuple[int, list[dict]]:
    return _logistic_score((weights or WEIGHTS)["arrival"], arrival_inputs(row))


# ---------------------------------------------------------------- Demand

def expected_occupancy(row: dict, weights: dict | None = None) -> tuple[float, float, list[dict]]:
    """Devuelve (ocupacion esperada, ocupacion normal, factores) como fraccion del aforo."""
    w = (weights or WEIGHTS)["demand"]
    base = base_demand(row["hour"], row["weekday"])
    effects = {
        "rain": -w["rain"] * rain_norm(row["rain_mm_h"]),
        "pop": -w["pop"] * row["pop"],
        "traffic": -w["traffic"] * row["congestion"],
        "heat": -w["heat"] * min(max(row["temp_c"] - 29, 0) / 6, 1),
        "cold": -w["cold"] * min(max(12 - row["temp_c"], 0) / 6, 1),
    }
    multiplier = max(1.0 + sum(effects.values()), 0.3)
    occ = min(base * multiplier, 1.2)
    factors = [{"factor": k, "impact": round(v, 3)} for k, v in effects.items()]
    factors.sort(key=lambda f: f["impact"])
    return round(occ, 3), base, factors


def demand_score(row: dict, weights: dict | None = None) -> tuple[int, str, dict]:
    """Riesgo por demanda anormal (baja o saturacion). Devuelve (score, direccion, detalle)."""
    occ, base, factors = expected_occupancy(row, weights)
    drop = (base - occ) / base if base > 0 else 0.0
    drop_score = 100 * min(max(drop, 0) / 0.35, 1.0)          # caida de 35% o mas = 100
    overflow_score = 100 * min(max(occ - 0.85, 0) / 0.20, 1.0)  # pasar 85% del aforo
    if overflow_score > drop_score:
        direction = "high"
        score = overflow_score
    elif drop_score >= 15:
        direction = "low"
        score = drop_score
    else:
        direction = "normal"
        score = max(drop_score, overflow_score)
    total = sum(abs(f["impact"]) for f in factors) or 1.0
    for f in factors:
        f["share_pct"] = round(abs(f["impact"]) / total * 100)
    return round(score), direction, {"occupancy": occ, "base": base, "drop_pct": round(drop * 100, 1), "factors": factors}


# ---------------------------------------------------------------- Cost

def cost_inputs(macro: dict | None) -> dict[str, float]:
    macro = macro or {}
    fx_change = macro.get("fx_change_30d_pct") or 0.0
    food = macro.get("food_inflation_12m_pct")
    return {
        "fx_up": min(max(fx_change, 0) / 2.0, 1.5),            # +2% en 30 dias = 1
        "food_inflation": min(max((food if food is not None else 2.0) - 2.0, 0) / 2.0, 1.5),  # sobre 2% anual
    }


def cost_score(macro: dict | None, weights: dict | None = None) -> tuple[int, list[dict]]:
    return _logistic_score((weights or WEIGHTS)["cost"], cost_inputs(macro))


def overall_score(scores: dict[str, int]) -> int:
    """Combina los riesgos: domina el peor, pero el resto tambien pesa."""
    values = list(scores.values())
    if not values:
        return 0
    weighted = 0.30 * scores.get("demand", 0) + 0.30 * scores.get("delivery", 0) + 0.20 * scores.get("arrival", 0) + 0.20 * scores.get("cost", 0)
    return round(0.6 * max(values) + 0.4 * weighted)
