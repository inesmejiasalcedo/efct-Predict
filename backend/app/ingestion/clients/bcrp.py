"""Cliente de BCRPData (Banco Central de Reserva del Peru). API publica, sin key.

Responsable: Harry.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.ingestion.clients.base import BaseClient

FX_SERIES = "PD04638PD"         # Tipo de cambio interbancario venta (diario)
FOOD_CPI_SERIES = "PN09822PM"   # IPC alimentos y bebidas, var% 12 meses (mensual)


class BcrpClient(BaseClient):
    BASE_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"

    def series(self, code: str, start: str, end: str) -> dict:
        return self._get_json(f"{self.BASE_URL}/{code}/json/{start}/{end}")

    def fx_last_days(self, days: int = 70, today: date | None = None) -> dict:
        today = today or date.today()
        start = today - timedelta(days=days)
        return self.series(FX_SERIES, f"{start.year}-{start.month}-{start.day}", f"{today.year}-{today.month}-{today.day}")

    def food_cpi_last_months(self, months: int = 14, today: date | None = None) -> dict:
        today = today or date.today()
        y, m = today.year, today.month - months
        while m <= 0:
            m += 12
            y -= 1
        return self.series(FOOD_CPI_SERIES, f"{y}-{m}", f"{today.year}-{today.month}")
