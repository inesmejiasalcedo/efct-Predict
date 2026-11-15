"""Pruebas del consumo de APIs y limpieza de datos (Harry). No usan internet."""
import pytest

from app.ingestion import cleaning
from app.ingestion.clients.base import ApiError
from app.ingestion.clients.bcrp import BcrpClient
from app.ingestion.clients.openweather import OpenWeatherClient
from app.ingestion.clients.tomtom import TomTomClient
from tests.conftest import FakeResponse, FakeSession

OW_CURRENT = {
    "dt": 1793664000,
    "main": {"temp": 19.4, "feels_like": 19.0, "humidity": 82},
    "weather": [{"main": "Drizzle", "description": "llovizna"}],
    "rain": {"1h": 0.4},
    "wind": {"speed": 3.6},
}
OW_FORECAST = {
    "list": [
        {"dt": 1793664000, "main": {"temp": 19}, "pop": 0.6, "rain": {"3h": 1.5}, "weather": [{"main": "Rain"}]},
        {"dt": 1793674800, "main": {"temp": 18}, "pop": 0.2, "weather": [{"main": "Clouds"}]},
        {"dt": 1793674800, "main": {"temp": 18}, "pop": 0.2, "weather": [{"main": "Clouds"}]},  # duplicado
        {"dt": 1793685600, "main": {}, "pop": 0.1},  # incompleto
    ]
}
TOMTOM = {"flowSegmentData": {"currentSpeed": 18, "freeFlowSpeed": 45, "currentTravelTime": 300, "freeFlowTravelTime": 120, "confidence": 0.9}}
BCRP_FX = {"periods": [{"name": "30.Oct.26", "values": ["3.761"]}, {"name": "29.Oct.26", "values": ["n.d."]}, {"name": "28.Oct.26", "values": ["3.749"]}]}


# ---------- clientes ----------

def test_openweather_client_sends_key_and_coords():
    session = FakeSession({"/weather": FakeResponse(OW_CURRENT)})
    raw = OpenWeatherClient("KEY123", session).current(-12.1, -77.0)
    assert raw["main"]["temp"] == 19.4
    url, params = session.calls[0]
    assert params["appid"] == "KEY123" and params["units"] == "metric" and params["lat"] == -12.1


def test_client_reports_invalid_key():
    session = FakeSession({"flowSegmentData": FakeResponse({}, 403)})
    with pytest.raises(ApiError, match="invalid_api_key"):
        TomTomClient("BAD", session).flow(-12.1, -77.0)


def test_client_without_key_fails_fast():
    with pytest.raises(ApiError, match="missing_api_key"):
        OpenWeatherClient("")


def test_bcrp_client_builds_url():
    session = FakeSession({"PD04638PD/json": FakeResponse(BCRP_FX)})
    BcrpClient(session).fx_last_days()
    assert "PD04638PD/json/" in session.calls[0][0]


# ---------- limpieza ----------

def test_clean_current_weather():
    w = cleaning.clean_current_weather(OW_CURRENT)
    assert w["temp_c"] == 19.4 and w["rain_mm_h"] == 0.4 and w["humidity"] == 82
    with pytest.raises(cleaning.CleaningError):
        cleaning.clean_current_weather({"main": {}})


def test_clean_weather_clips_out_of_range():
    w = cleaning.clean_current_weather({"main": {"temp": 99, "humidity": 140}, "rain": {"1h": -3}})
    assert w["temp_c"] == 55 and w["humidity"] == 100 and w["rain_mm_h"] == 0


def test_clean_forecast_expands_hourly_and_dedupes():
    hourly = cleaning.clean_forecast(OW_FORECAST)
    assert len(hourly) == 6  # 2 bloques validos x 3 horas (duplicado e incompleto descartados)
    assert hourly[0]["rain_mm_h"] == 0.5  # 1.5 mm en 3 horas
    assert len({h["time"] for h in hourly}) == 6


def test_clean_traffic_congestion():
    t = cleaning.clean_traffic(TOMTOM)
    assert t["congestion"] == pytest.approx(0.6, abs=0.001)  # 1 - 18/45
    assert t["travel_time_ratio"] == 2.5
    with pytest.raises(cleaning.CleaningError):
        cleaning.clean_traffic({"flowSegmentData": {"currentSpeed": 10, "freeFlowSpeed": 0}})


def test_clean_bcrp_parses_periods_and_skips_nd():
    pts = cleaning.clean_bcrp_series(BCRP_FX)
    assert [p["period"] for p in pts] == ["2026-10-28", "2026-10-30"]
    assert cleaning.parse_bcrp_period("Set.2026") == "2026-09"


def test_summarize_macro_fx_change():
    fx = [{"period": "2026-09-01", "value": 3.70}, {"period": "2026-10-15", "value": 3.75}, {"period": "2026-10-31", "value": 3.774}]
    m = cleaning.summarize_macro(fx, [{"period": "2026-09", "value": 3.1}])
    assert m["fx_change_30d_pct"] == 2.0
    assert m["food_inflation_12m_pct"] == 3.1


# ---------- pipeline completo ----------

def _owner_site(db):
    from app.business.models import Restaurant, Site
    from app.iam.models import User

    u = User(email="p@test.pe", password_hash="x")
    db.add(u)
    db.flush()
    r = Restaurant(owner_id=u.id, name="R")
    db.add(r)
    db.flush()
    s = Site(restaurant_id=r.id, name="S", lat=-12.1, lon=-77.0, capacity=40, open_hour=12, close_hour=23)
    db.add(s)
    db.commit()
    return s


def test_pipeline_uses_real_api_when_key_present(client, monkeypatch):
    from app.config import settings
    from app.ingestion import service
    from app.shared.db import SessionLocal

    monkeypatch.setattr(settings, "openweather_api_key", "K1")
    monkeypatch.setattr(settings, "tomtom_api_key", "K2")
    session = FakeSession(
        {
            "/weather": FakeResponse(OW_CURRENT),
            "/forecast": FakeResponse(OW_FORECAST),
            "flowSegmentData": FakeResponse(TOMTOM),
            "PD04638PD": FakeResponse(BCRP_FX),
            "PN09822PM": FakeResponse({"periods": [{"name": "Set.2026", "values": ["3.2"]}]}),
        }
    )
    with SessionLocal() as db:
        site = _owner_site(db)
        results = service.refresh_site(db, site, session=session)
        assert all(r["status"] == "ok" for r in results), results
        snap = service.latest(db, "traffic", site.id)
        assert snap.is_simulated is False and snap.payload["congestion"] == pytest.approx(0.6, abs=0.001)


def test_pipeline_keeps_last_good_data_when_api_fails(client, monkeypatch):
    from app.config import settings
    from app.ingestion import service
    from app.shared.db import SessionLocal

    monkeypatch.setattr(settings, "tomtom_api_key", "K2")
    with SessionLocal() as db:
        site = _owner_site(db)
        service.refresh_traffic(db, site, session=FakeSession({"flowSegmentData": FakeResponse(TOMTOM)}))
        result = service.refresh_traffic(db, site, session=FakeSession({"flowSegmentData": FakeResponse({}, 500)}))
        assert result["status"] == "error_using_last"
        assert service.latest(db, "traffic", site.id).is_simulated is False


def test_pipeline_simulates_without_keys(client):
    from app.ingestion import service
    from app.shared.db import SessionLocal

    with SessionLocal() as db:
        site = _owner_site(db)
        result = service.refresh_traffic(db, site)
        assert result["status"] == "simulated"
        assert service.latest(db, "traffic", site.id).is_simulated is True
