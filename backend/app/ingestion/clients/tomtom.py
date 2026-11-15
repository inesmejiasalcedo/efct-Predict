"""Cliente de TomTom Traffic Flow. Responsable: Harry."""
from __future__ import annotations

from app.ingestion.clients.base import ApiError, BaseClient


class TomTomClient(BaseClient):
    FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

    def __init__(self, api_key: str, session=None) -> None:
        if not api_key:
            raise ApiError("missing_api_key")
        super().__init__(session)
        self.api_key = api_key

    def flow(self, lat: float, lon: float) -> dict:
        return self._get_json(self.FLOW_URL, {"point": f"{lat},{lon}", "key": self.api_key, "unit": "KMPH"})
