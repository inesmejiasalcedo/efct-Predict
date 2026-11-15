"""Base comun de los clientes HTTP. Responsable: Harry.

Cada cliente recibe una "session" inyectable: en produccion es requests, en las pruebas
es un objeto falso que devuelve respuestas grabadas (asi probamos sin internet).
"""
from __future__ import annotations

import requests

TIMEOUT_SECONDS = 15


class ApiError(RuntimeError):
    """Error al consultar una API externa (red, credenciales o respuesta invalida)."""


class BaseClient:
    def __init__(self, session=None) -> None:
        self.session = session or requests.Session()

    def _get_json(self, url: str, params: dict | None = None):
        try:
            response = self.session.get(url, params=params, timeout=TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            raise ApiError(f"network_error: {exc.__class__.__name__}") from exc
        status = getattr(response, "status_code", 200)
        if status in (401, 403):
            raise ApiError("invalid_api_key")
        if status == 429:
            raise ApiError("rate_limited")
        if status >= 400:
            raise ApiError(f"http_{status}")
        try:
            return response.json()
        except ValueError as exc:
            raise ApiError("invalid_json") from exc
