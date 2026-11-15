"""Endpoints del dashboard.

/summary  -> pagina de Resumen (Ines): estado general, 4 riesgos, curva del dia, acciones.
/risk/... -> paginas de Detalle (Diana): un riesgo con sus factores, serie horaria y datos.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.business.service import get_site_for_user
from app.iam.deps import get_current_user
from app.iam.models import User
from app.ingestion import service as data
from app.ingestion.models import SOURCE_FORECAST, SOURCE_MACRO
from app.prediction.risk import RISK_TYPES
from app.reporting.service import site_prediction
from app.shared.db import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Que serie horaria y que datos externos acompanan a cada riesgo en su pagina de detalle
DETAIL_SERIES = {
    "demand": ["expected_guests", "normal_guests", "rain_mm_h"],
    "delivery": ["delivery", "congestion", "rain_mm_h"],
    "arrival": ["arrival", "congestion", "rain_mm_h"],
    "cost": [],
}


_backtest_cache: dict = {}


@router.get("/model")
def model_quality(_: User = Depends(get_current_user)):
    """Resultado del backtesting (precision del modelo) para mostrarlo en la interfaz."""
    if "result" not in _backtest_cache:
        from app.prediction.backtest import run_backtest

        _backtest_cache["result"] = run_backtest()
    return _backtest_cache["result"]


@router.get("/summary")
def summary(site_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """HU (Ines): Como gerente quiero ver en una sola pantalla como viene el dia y que hacer."""
    site = get_site_for_user(db, user, site_id)
    return site_prediction(db, site)


@router.get("/risk/{risk_type}")
def risk_detail(risk_type: str, site_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """HU (Diana): Como gerente quiero entender por que un riesgo esta alto y que lo causa."""
    if risk_type not in RISK_TYPES:
        raise HTTPException(404, detail="risk_not_found")
    site = get_site_for_user(db, user, site_id)
    pred = site_prediction(db, site)
    risk = next(r for r in pred["risks"] if r["type"] == risk_type)
    keys = DETAIL_SERIES[risk_type]
    series = [
        {"time": h["time"], "hour": h["hour"], "in_service": h["in_service"], **{k: h[k] for k in keys}}
        for h in pred["hourly"]
    ]
    macro_snap = data.latest(db, SOURCE_MACRO, None)
    forecast_snap = data.latest(db, SOURCE_FORECAST, site.id)
    return {
        "site": pred["site"],
        "risk": risk,
        "series": series,
        "inputs": {
            "weather": pred["current"]["weather"],
            "traffic": pred["current"]["traffic"],
            "macro": macro_snap.payload if (macro_snap and risk_type == "cost") else pred["current"]["macro"],
            "forecast_hours": len(forecast_snap.payload or []) if forecast_snap else 0,
        },
        "data_status": pred["data_status"],
        "generated_at": pred["generated_at"],
    }
