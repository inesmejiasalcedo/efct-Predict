"""Recomendaciones accionables segun el riesgo. Responsable: Diana.

El backend devuelve codigos + parametros; el frontend los traduce (ES/EN) a frases como
"Avisa al personal que salga 20 min antes". Asi la traduccion vive en un solo lugar.
"""
from __future__ import annotations


def _window(w: dict | None) -> dict:
    return {"from": w["from"], "to": w["to"]} if w else {}


def actions_for(risk: dict) -> list[dict]:
    rtype, score, level = risk["type"], risk["score"], risk["level"]
    top = risk["factors"][0]["factor"] if risk.get("factors") else None
    win = _window(risk.get("window"))
    out: list[dict] = []

    if rtype == "demand":
        direction = risk.get("direction")
        if direction == "low" and score >= 40:
            pct = int(min(max(risk.get("detail", {}).get("drop_pct", 15), 10), 40) // 5 * 5)
            out.append({"code": "prep_less", "params": {"pct": pct, **win}})
            if top in ("rain", "pop"):
                out.append({"code": "push_delivery", "params": win})
            out.append({"code": "reduce_shift", "params": win})
        elif direction == "high" and score >= 40:
            out.append({"code": "extra_staff", "params": win})
            out.append({"code": "prep_more", "params": win})
            out.append({"code": "manage_queue", "params": win})
        else:
            out.append({"code": "demand_normal", "params": {}})

    elif rtype == "delivery":
        if score >= 40:
            minutes = 10 if level == "medium" else 20
            out.append({"code": "delivery_buffer", "params": {"minutes": minutes, **win}})
            if top in ("rain", "pop"):
                out.append({"code": "rain_packaging", "params": win})
            if top in ("congestion", "volatility", "peak"):
                out.append({"code": "nearby_orders", "params": win})
            if level == "high":
                out.append({"code": "extra_riders", "params": win})
        else:
            out.append({"code": "delivery_normal", "params": {}})

    elif rtype == "arrival":
        if score >= 40:
            minutes = 15 if level == "medium" else 30
            out.append({"code": "staff_early", "params": {"minutes": minutes, "hour": risk.get("hour")}})
            out.append({"code": "supplier_early", "params": {"hour": risk.get("hour")}})
        else:
            out.append({"code": "arrival_normal", "params": {}})

    elif rtype == "cost":
        if score >= 40:
            if top == "fx_up":
                out.append({"code": "buy_imported_ahead", "params": {}})
            out.append({"code": "review_prices", "params": {}})
            out.append({"code": "check_suppliers", "params": {}})
        else:
            out.append({"code": "cost_normal", "params": {}})

    priority = {"high": 1, "medium": 2, "low": 3}[level]
    for a in out:
        a["risk"] = rtype
        a["priority"] = priority
    return out
