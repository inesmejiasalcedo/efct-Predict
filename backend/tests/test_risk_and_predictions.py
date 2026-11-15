"""Pruebas de calculos de riesgo, predicciones y backtesting (Harry, Ines, Diana)."""
from datetime import datetime, timezone

from app.prediction import risk as R
from app.prediction.backtest import run_backtest
from app.prediction.features import ExternalData, SiteContext, build_hourly_features, project_congestion
from app.prediction.forecast import predict
from app.prediction.profiles import to_local
from tests.conftest import SITE, register


def row(**kw):
    base = {"hour": 20, "weekday": 2, "in_service": True, "peak": True, "rain_mm_h": 0.0, "pop": 0.0,
            "temp_c": 20.0, "congestion": 0.2, "volatility": 0.0}
    base.update(kw)
    return base


# ---------- calculos de riesgo ----------

def test_delivery_risk_grows_with_traffic_and_rain():
    calm = R.delivery_score(row(congestion=0.1))[0]
    jam = R.delivery_score(row(congestion=0.7))[0]
    jam_rain = R.delivery_score(row(congestion=0.7, rain_mm_h=2.5, pop=0.9))[0]
    assert calm < jam < jam_rain
    assert 0 <= calm and jam_rain <= 100


def test_levels():
    assert R.level_for(10) == "low" and R.level_for(40) == "medium" and R.level_for(70) == "high"


def test_rescale_puts_threshold_at_50():
    assert R.rescale_to_threshold(28, 28) == 50
    assert R.rescale_to_threshold(0, 28) == 0
    assert R.rescale_to_threshold(100, 28) == 100


def test_rain_lowers_expected_occupancy():
    dry, base, _ = R.expected_occupancy(row())
    wet, _, _ = R.expected_occupancy(row(rain_mm_h=3, pop=1))
    assert wet < dry <= base


def test_demand_detects_low_demand_with_heavy_rain():
    score, direction, detail = R.demand_score(row(rain_mm_h=4, pop=1, congestion=0.6))
    assert direction == "low" and score >= 40 and detail["drop_pct"] > 15


def test_cost_risk_grows_with_exchange_rate_and_inflation():
    calm = R.cost_score({"fx_change_30d_pct": 0, "food_inflation_12m_pct": 2.0})[0]
    hot = R.cost_score({"fx_change_30d_pct": 3, "food_inflation_12m_pct": 6.0})[0]
    assert calm < 40 <= hot


def test_overall_dominated_by_worst_risk():
    assert R.overall_score({"demand": 10, "delivery": 90, "arrival": 10, "cost": 10}) >= 60


# ---------- predicciones ----------

NOW = datetime(2026, 11, 6, 22, 0, tzinfo=timezone.utc)  # viernes 17:00 en Lima


def _ext(rain=0.0):
    forecast = [
        {"time": f"2026-11-{6 + (22 + i) // 24:02d}T{(22 + i) % 24:02d}:00:00Z", "temp_c": 19, "pop": 0.8 if rain else 0.1, "rain_mm_h": rain, "condition": "Rain"}
        for i in range(30)
    ]
    return ExternalData(
        weather={"temp_c": 19, "rain_mm_h": rain},
        forecast=forecast,
        traffic={"congestion": 0.45},
        traffic_history=[0.3, 0.4, 0.45],
        macro={"fx_change_30d_pct": 0.5, "food_inflation_12m_pct": 2.5},
    )


def test_features_cover_next_24_hours():
    rows = build_hourly_features(SiteContext(60, 12, 23), _ext(), now_utc=NOW)
    assert len(rows) == 24
    assert rows[0]["hour"] == 17 and rows[0]["weekday"] == 4
    assert rows[0]["in_service"] is True and rows[7]["in_service"] is False  # 24:00 cerrado


def test_congestion_projection_decays_to_typical():
    now = to_local(NOW)
    near = project_congestion(0.9, now, now)
    far = project_congestion(0.9, now, now.replace(hour=23))
    assert near > far


def test_prediction_structure_and_closed_hours():
    ctx = SiteContext(60, 12, 23)
    result = predict(ctx, build_hourly_features(ctx, _ext(), now_utc=NOW), _ext().macro)
    assert [r["type"] for r in result["risks"]] == ["demand", "delivery", "arrival", "cost"]
    assert len(result["hourly"]) == 24
    closed = [h for h in result["hourly"] if not h["in_service"]]
    assert closed and all(h["expected_guests"] == 0 for h in closed)
    assert result["overall"]["level"] in ("low", "medium", "high")
    for r in result["risks"]:
        assert r["actions"], r["type"]


def test_rainy_night_increases_delivery_risk_and_lowers_guests():
    ctx = SiteContext(60, 12, 23)
    dry = predict(ctx, build_hourly_features(ctx, _ext(0.0), now_utc=NOW), None)
    wet = predict(ctx, build_hourly_features(ctx, _ext(3.0), now_utc=NOW), None)
    risk = lambda res, t: next(r for r in res["risks"] if r["type"] == t)  # noqa: E731
    assert risk(wet, "delivery")["score"] > risk(dry, "delivery")["score"]
    assert sum(h["expected_guests"] for h in wet["hourly"]) < sum(h["expected_guests"] for h in dry["hourly"])
    assert any(a["code"] == "delivery_buffer" for a in risk(wet, "delivery")["actions"])


def test_summary_endpoint_end_to_end(client):
    h = register(client)
    site_id = client.post("/api/business/sites", headers=h, json=SITE).json()["id"]
    r = client.get("/api/dashboard/summary", headers=h, params={"site_id": site_id})
    assert r.status_code == 200
    body = r.json()
    assert len(body["risks"]) == 4 and len(body["hourly"]) == 24
    assert set(body["data_status"]["simulated_sources"]) == {"weather", "forecast", "traffic", "macro"}
    detail = client.get("/api/dashboard/risk/delivery", headers=h, params={"site_id": site_id}).json()
    assert detail["risk"]["type"] == "delivery" and len(detail["series"]) == 24


# ---------- backtesting ----------

def test_backtest_meets_minimum_thresholds():
    result = run_backtest()
    assert result["dataset"]["test"] > 1000
    assert result["delivery"]["accuracy"] >= 0.75
    assert result["delivery"]["f1"] >= 0.60
    assert result["demand"]["mae"] <= 0.10
    assert result["passed"] is True
