"""Calibra (optimiza) los pesos del modelo con el historico. Responsable: Harry.

  delivery: regresion logistica entrenada por descenso de gradiente (minimiza log-loss),
            luego se elige el umbral que maximiza F1 en entrenamiento.
  demanda:  busqueda en grilla de los efectos de lluvia, probabilidad de lluvia y trafico
            que minimiza el error absoluto medio.

Solo usa el 70% mas antiguo del historico; el 30% restante queda para evaluar.
Uso (desde backend/):  python -m scripts.calibrate
"""
from __future__ import annotations

import copy
import itertools
import json
import math

from app.prediction import risk as R
from app.prediction.backtest import (
    evaluate_delivery,
    load_history,
    run_backtest,
    temporal_split,
)

FEATURES = ["congestion", "rain", "peak", "volatility", "pop"]


def fit_logistic(rows, epochs: int = 3000, lr: float = 3.0, l2: float = 0.001):
    xs = [R.delivery_inputs(r) for r in rows]
    ys = [r["delivery_delay_incident"] for r in rows]
    w = {f: 0.0 for f in FEATURES}
    b = 0.0
    n = len(xs)
    for _ in range(epochs):
        gw = {f: 0.0 for f in FEATURES}
        gb = 0.0
        for x, y in zip(xs, ys):
            p = 1 / (1 + math.exp(-(b + sum(w[f] * x[f] for f in FEATURES))))
            err = p - y
            gb += err
            for f in FEATURES:
                gw[f] += err * x[f]
        b -= lr * gb / n
        for f in FEATURES:
            w[f] -= lr * (gw[f] / n + l2 * w[f])
    return b, w


def best_threshold(rows, weights):
    best = (0, 50)
    for t in range(20, 81, 2):
        trial = dict(weights, threshold=t)
        f1 = evaluate_delivery(rows, trial)["f1"]
        if f1 > best[0]:
            best = (f1, t)
    return best[1]


def fit_demand(rows, weights):
    best = (9.9, None)
    for rain, pop, traffic in itertools.product([0.15, 0.2, 0.25, 0.3, 0.35], [0.0, 0.05, 0.1, 0.15], [0.0, 0.1, 0.15, 0.2]):
        trial = copy.deepcopy(weights)
        trial["demand"].update({"rain": rain, "pop": pop, "traffic": traffic})
        mae = sum(abs(R.expected_occupancy(r, trial)[0] - r["occupancy_actual"]) for r in rows) / len(rows)
        if mae < best[0]:
            best = (mae, {"rain": rain, "pop": pop, "traffic": traffic})
    return best[1]


def main() -> None:
    rows = load_history()
    train, _ = temporal_split(rows)
    weights = copy.deepcopy(R.WEIGHTS)

    before = run_backtest(weights)
    b, w = fit_logistic(train)
    weights["delivery"] = {"bias": round(b, 3), **{f: round(v, 3) for f, v in w.items()}}
    weights["threshold"] = best_threshold(train, weights)
    weights["demand"].update(fit_demand(train, weights))
    after = run_backtest(weights)

    R.WEIGHTS_PATH.write_text(json.dumps(weights, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Antes :", json.dumps({"delivery": before["delivery"], "demand": before["demand"]}, indent=1))
    print("Despues:", json.dumps({"delivery": after["delivery"], "demand": after["demand"]}, indent=1))
    print("Aprobado:", after["passed"], "| pesos guardados en", R.WEIGHTS_PATH)


if __name__ == "__main__":
    main()
