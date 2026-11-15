"""Genera un historico SIMULADO para backtesting del modelo. Responsable: Harry.

IMPORTANTE: este historico es sintetico. Simula un ano de operacion (horas de servicio)
con un proceso "real" distinto al del modelo (otras formas funcionales + ruido), para
medir si el modelo generaliza. Cuando el restaurante registre incidentes reales, se
reemplaza este CSV por los datos reales con las mismas columnas.

Uso (desde backend/):  python -m scripts.generate_backtest_data
"""
from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

from app.prediction.profiles import typical_congestion

OUT = Path(__file__).resolve().parent.parent / "data" / "backtest" / "history.csv"
SEED = 2026
DAYS = 365
OPEN, CLOSE = 11, 23


def sigmoid(z: float) -> float:
    return 1 / (1 + math.exp(-z))


def true_base_demand(hour: int, weekday: int) -> float:
    """Demanda 'real' del restaurante: parecida pero NO igual a la curva del modelo."""
    lunch = 0.66 * math.exp(-((hour - 13.0) ** 2) / (2 * 1.3 ** 2))
    dinner = 0.64 * math.exp(-((hour - 20.5) ** 2) / (2 * 1.3 ** 2))
    if weekday in (4, 5):
        dinner *= 1.25
    if weekday == 6:
        lunch *= 1.35
        dinner *= 0.65
    if weekday == 0:
        lunch *= 0.88
        dinner *= 0.82
    return min(0.07 + lunch + dinner, 1.0)


def main() -> None:
    rnd = random.Random(SEED)
    start = date(2025, 11, 1)
    rows = []
    for d in range(DAYS):
        day = start + timedelta(days=d)
        wd = day.weekday()
        summer = day.month in (12, 1, 2, 3, 4)
        rainy_day = rnd.random() < (0.10 if summer else 0.22)
        base_temp = 24 if summer else 18
        for hour in range(OPEN, CLOSE):
            pop = min(1.0, (0.6 if rainy_day else 0.05) + rnd.uniform(0, 0.3))
            raining = rainy_day and rnd.random() < 0.55
            rain = round(rnd.expovariate(1 / 0.9), 2) if raining else 0.0
            temp = round(base_temp + 3 * math.sin((hour - 9) / 24 * 2 * math.pi) + rnd.uniform(-1.5, 1.5), 1)
            accident = rnd.random() < 0.04
            congestion = typical_congestion(hour, wd) + rnd.gauss(0, 0.07) + 0.10 * min(rain / 2, 1) + (0.25 if accident else 0)
            congestion = round(min(max(congestion, 0.0), 0.95), 3)
            volatility = round(min(max(rnd.gauss(0.05, 0.03) + (0.12 if accident else 0), 0), 0.4), 3)
            peak = 1 if (12 <= hour <= 14 or 19 <= hour <= 21) else 0

            # Proceso real de retrasos en delivery (>15 min sobre lo prometido)
            z = -3.6 + 5.0 * congestion ** 1.15 + 2.4 * min(rain / 2, 1) ** 0.8 + 0.8 * peak + 1.3 * min(volatility / 0.2, 1) + rnd.gauss(0, 0.45)
            delay_incident = 1 if rnd.random() < sigmoid(3.0 * z) else 0

            # Proceso real de ocupacion del salon
            rain_n = min(rain / 2, 1)
            occ = true_base_demand(hour, wd) * (1 - 0.30 * rain_n - 0.08 * pop - 0.14 * congestion)
            occ *= math.exp(rnd.gauss(0, 0.10))
            occ = round(min(max(occ, 0.0), 1.2), 3)

            rows.append(
                {
                    "date": day.isoformat(),
                    "hour": hour,
                    "weekday": wd,
                    "rain_mm_h": rain,
                    "pop": round(pop, 2),
                    "temp_c": temp,
                    "congestion": congestion,
                    "volatility": volatility,
                    "peak": peak,
                    "delivery_delay_incident": delay_incident,
                    "occupancy_actual": occ,
                }
            )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Historico simulado: {len(rows)} filas -> {OUT}")


if __name__ == "__main__":
    main()
