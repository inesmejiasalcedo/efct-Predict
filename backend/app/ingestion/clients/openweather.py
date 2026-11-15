"""Cliente de OpenWeather (clima actual y pronostico 5 dias / 3 horas). Responsable: Harry."""
from __future__ import annotations

from app.ingestion.clients.base import ApiError, BaseClient


class OpenWeatherClient(BaseClient):
    CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
    FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

    def __init__(self, api_key: str, session=None) -> None:
        if not api_key:
            raise ApiError("missing_api_key")
        super().__init__(session)
        self.api_key = api_key

    def _params(self, lat: float, lon: float) -> dict:
        return {"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric", "lang": "es"}

    def current(self, lat: float, lon: float) -> dict:
        return self._get_json(self.CURRENT_URL, self._params(lat, lon))

    def forecast(self, lat: float, lon: float) -> dict:
        return self._get_json(self.FORECAST_URL, self._params(lat, lon))
