"""Backtesting: mide la precision del modelo contra un historico. Responsable: Harry.

Particion temporal: el 70% mas antiguo se usa para calibrar y el 30% mas reciente para
evaluar (asi se simula predecir el futuro con lo aprendido del pasado).

Umbrales minimos de aceptacion (los verifica tests/test_backtest.py):
  delivery: accuracy >= 0.75 y F1 >= 0.60 en el conjunto de prueba
  demanda:  error absoluto medio (MAE) <= 0.10 del aforo
"""
from __future__ import annotations

import csv
from pathlib import Path

from app.prediction import risk as R

HISTORY_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "backtest" / "history.csv"

MIN_ACCURACY = 0.75
MIN_F1 = 0.60
MAX_DEMAND_MAE = 0.10


def load_history(path: Path = HISTORY_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        rows = []
        for r in csv.DictReader(fh):
            rows.append(
                {
                    "date": r["date"],
                    "hour": int(r["hour"]),
                    "weekday": int(r["weekday"]),
                    "rain_mm_h": float(r["rain_mm_h"]),
                    "pop": float(r["pop"]),
                    "temp_c": float(r["temp_c"]),
                    "congestion": float(r["congestion"]),
                    "volatility": float(r["volatility"]),
                    "peak": r["peak"] == "1",
                    "in_service": True,
                    "delivery_delay_incident": int(r["delivery_delay_incident"]),
                    "occupancy_actual": float(r["occupancy_actual"]),
                }
            )
    rows.sort(key=lambda r: (r["date"], r["hour"]))
    return rows


def temporal_split(rows: list[dict], test_fraction: float = 0.3) -> tuple[list[dict], list[dict]]:
    cut = int(len(rows) * (1 - test_fraction))
    return rows[:cut], rows[cut:]


def classification_metrics(y_true: list[int], y_pred: list[int]) -> dict:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    n = max(len(y_true), 1)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "n": len(y_true),
        "accuracy": round((tp + tn) / n, 3),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "confusion": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
    }


def evaluate_delivery(rows: list[dict], weights: dict) -> dict:
    threshold = weights.get("threshold", 50)
    y_true = [r["delivery_delay_incident"] for r in rows]
    y_pred = [1 if R.delivery_probability(r, weights)[0] >= threshold else 0 for r in rows]
    metrics = classification_metrics(y_true, y_pred)
    metrics["threshold"] = threshold
    metrics["base_rate"] = round(sum(y_true) / max(len(y_true), 1), 3)
    return metrics


def evaluate_demand(rows: list[dict], weights: dict) -> dict:
    errors = [abs(R.expected_occupancy(r, weights)[0] - r["occupancy_actual"]) for r in rows]
    n = max(len(errors), 1)
    return {
        "n": len(errors),
        "mae": round(sum(errors) / n, 3),
        "within_10pts_pct": round(sum(1 for e in errors if e <= 0.10) / n * 100, 1),
    }


def run_backtest(weights: dict | None = None, path: Path = HISTORY_PATH) -> dict:
    weights = weights or R.WEIGHTS
    rows = load_history(path)
    train, test = temporal_split(rows)
    delivery = evaluate_delivery(test, weights)
    demand = evaluate_demand(test, weights)
    passed = delivery["accuracy"] >= MIN_ACCURACY and delivery["f1"] >= MIN_F1 and demand["mae"] <= MAX_DEMAND_MAE
    return {
        "dataset": {"rows": len(rows), "train": len(train), "test": len(test), "simulated": True},
        "delivery": delivery,
        "demand": demand,
        "thresholds": {"min_accuracy": MIN_ACCURACY, "min_f1": MIN_F1, "max_demand_mae": MAX_DEMAND_MAE},
        "passed": passed,
    }
