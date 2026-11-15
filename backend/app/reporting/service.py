"""Arma la prediccion de una sede a partir de los ultimos datos guardados.

Lo usan la pagina de Resumen (Ines) y las paginas de Detalle (Diana).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.business.models import Site
from app.business.service import price_stats
from app.ingestion import service as data
from app.ingestion.models import SOURCE_FORECAST, SOURCE_MACRO, SOURCE_TRAFFIC, SOURCE_WEATHER
from app.prediction.features import ExternalData, SiteContext, build_hourly_features
from app.prediction.forecast import predict


def load_external(db: Session, site: Site) -> ExternalData:
    ext = ExternalData()
    w = data.latest(db, SOURCE_WEATHER, site.id)
    f = data.latest(db, SOURCE_FORECAST, site.id)
    t = data.latest(db, SOURCE_TRAFFIC, site.id)
    m = data.latest(db, SOURCE_MACRO, None)
    if w:
        ext.weather = w.payload
    if f:
        ext.forecast = f.payload or []
    if t:
        ext.traffic = t.payload
    if m:
        ext.macro = m.payload
    ext.traffic_history = [s.payload.get("congestion", 0) for s in data.recent_traffic(db, site.id) if s.payload]
    ext.simulated_sources = [s.source for s in (w, f, t, m) if s is not None and s.is_simulated]
    return ext


def site_prediction(db: Session, site: Site, now: datetime | None = None) -> dict:
    # Si nunca se trajeron datos para esta sede, se traen ahora (primera visita)
    if data.latest(db, SOURCE_TRAFFIC, site.id) is None or data.latest(db, SOURCE_FORECAST, site.id) is None:
        data.refresh_site(db, site)
    ext = load_external(db, site)
    ctx = SiteContext(
        capacity=site.capacity,
        open_hour=site.open_hour,
        close_hour=site.close_hour,
        avg_menu_price=price_stats(site.restaurant.menu_items)["avg"],
    )
    rows = build_hourly_features(ctx, ext, now_utc=now or datetime.now(timezone.utc))
    result = predict(ctx, rows, ext.macro)
    result["site"] = {
        "id": site.id,
        "name": site.name,
        "district": site.district,
        "capacity": site.capacity,
        "open_hour": site.open_hour,
        "close_hour": site.close_hour,
    }
    result["current"] = {"weather": ext.weather, "traffic": ext.traffic, "macro": _macro_light(ext.macro)}
    result["data_status"] = {
        "keys": data.keys_configured(),
        "sources": data.source_status(db, site.id),
        "simulated_sources": ext.simulated_sources,
    }
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    return result


def _macro_light(macro: dict | None) -> dict | None:
    if not macro:
        return None
    return {k: macro.get(k) for k in ("fx_last", "fx_change_30d_pct", "food_inflation_12m_pct")}
