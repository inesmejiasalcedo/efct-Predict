"""Configuracion comun de pruebas: base de datos temporal, sin scheduler, sin API keys."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp()) / "test.db"
os.environ.update(
    {
        "DATABASE_URL": f"sqlite:///{_tmp.as_posix()}",
        "SCHEDULER_ENABLED": "false",
        "SECRET_KEY": "test-secret-key-solo-para-pruebas-0123456789",
        "ADMIN_EMAIL": "admin@efct.pe",
        "ADMIN_PASSWORD": "AdminPrueba1",
        "TOMTOM_API_KEY": "",
        "OPENWEATHER_API_KEY": "",
        "ALLOW_SIMULATED_DATA": "true",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.shared.db import Base, engine  # noqa: E402


class FakeResponse:
    def __init__(self, payload=None, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeSession:
    """Reemplaza a requests: devuelve respuestas grabadas segun la URL."""

    def __init__(self, routes: dict):
        self.routes = routes
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        for fragment, response in self.routes.items():
            if fragment in url:
                return response
        return FakeResponse({}, 404)


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:  # el lifespan crea las tablas y el admin
        yield c


def register(client, email="dueno@test.pe", password="Clave2026", name="13 Monjas"):
    r = client.post("/api/auth/register", json={"email": email, "password": password, "restaurant_name": name})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def admin_headers(client):
    r = client.post("/api/auth/login", json={"email": "admin@efct.pe", "password": "AdminPrueba1"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


SITE = {
    "name": "Sede Centro",
    "district": "Cercado de Arequipa",
    "lat": -16.3989,
    "lon": -71.5369,
    "capacity": 60,
    "open_hour": 12,
    "close_hour": 23,
}
