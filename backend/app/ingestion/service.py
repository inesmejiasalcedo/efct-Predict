"""Pipeline de datos: obtener -> limpiar -> guardar. Responsable: Harry.

Por cada fuente:
  1. Si hay API key, se consulta la API real y se limpia el resultado.
  2. Si falla, se registra el error y se sigue usando el ultimo dato valido.
  3. Si no hay key (o nunca hubo dato valido) y ALLOW_SIMULATED_DATA=true,
     se guarda un dato simulado marcado como tal.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.business.models import Site
from app.config import settings
from app.ingestion import cleaning, simulated
from app.ingestion.clients.base import ApiError
from app.ingestion.clients.bcrp import BcrpClient
from app.ingestion.clients.openweather import OpenWeatherClient
from app.ingestion.clients.tomtom import TomTomClient
from app.ingestion.models import (
    SOURCE_FORECAST,
    SOURCE_MACRO,
    SOURCE_TRAFFIC,
    SOURCE_WEATHER,
    Snapshot,
)
from app.shared.db import utcnow

# Despues de cuanto tiempo un dato se considera viejo (minutos)
STALE_AFTER = {SOURCE_WEATHER: 90, SOURCE_FORECAST: 180, SOURCE_TRAFFIC: 45, SOURCE_MACRO: 60 * 48}
RETENTION_DAYS = 30


def latest(db: Session, source: str, site_id: int | None, ok_only: bool = True) -> Snapshot | None:
    q = select(Snapshot).where(Snapshot.source == source)
    q = q.where(Snapshot.site_id.is_(None)) if site_id is None else q.where(Snapshot.site_id == site_id)
    if ok_only:
        q = q.where(Snapshot.ok.is_(True))
    return db.scalar(q.order_by(Snapshot.fetched_at.desc(), Snapshot.id.desc()).limit(1))


def recent_traffic(db: Session, site_id: int, minutes: int = 90) -> list[Snapshot]:
    since = utcnow() - timedelta(minutes=minutes)
    q = (
        select(Snapshot)
        .where(Snapshot.source == SOURCE_TRAFFIC, Snapshot.site_id == site_id, Snapshot.ok.is_(True))
        .where(Snapshot.fetched_at >= since)
        .order_by(Snapshot.fetched_at)
    )
    return list(db.scalars(q).all())


def _save(db: Session, source: str, site_id: int | None, payload=None, simulated_flag=False, error=None) -> Snapshot:
    snap = Snapshot(
        source=source,
        site_id=site_id,
        payload=payload,
        is_simulated=simulated_flag,
        ok=error is None,
        error=error,
    )
    db.add(snap)
    db.commit()
    return snap


def _has_fresh_real(db: Session, source: str, site_id: int | None) -> bool:
    snap = latest(db, source, site_id)
    if snap is None or snap.is_simulated:
        return False
    return utcnow() - snap.fetched_at < timedelta(minutes=STALE_AFTER[source] * 4)


def _run_source(db: Session, source: str, site_id: int | None, has_key: bool, fetch_real, make_simulated) -> dict:
    if has_key:
        try:
            payload = fetch_real()
            _save(db, source, site_id, payload)
            return {"source": source, "status": "ok", "simulated": False}
        except (ApiError, cleaning.CleaningError) as exc:
            _save(db, source, site_id, error=str(exc)[:300])
            if _has_fresh_real(db, source, site_id):
                return {"source": source, "status": "error_using_last", "error": str(exc)}
            error = str(exc)
    else:
        error = "missing_api_key"
    if settings.allow_simulated_data:
        _save(db, source, site_id, make_simulated(), simulated_flag=True)
        return {"source": source, "status": "simulated", "simulated": True, "reason": error}
    return {"source": source, "status": "unavailable", "error": error}


def refresh_weather(db: Session, site: Site, session=None) -> list[dict]:
    client = OpenWeatherClient(settings.openweather_api_key, session) if settings.has_openweather else None
    return [
        _run_source(
            db, SOURCE_WEATHER, site.id, client is not None,
            lambda: cleaning.clean_current_weather(client.current(site.lat, site.lon)),
            lambda: simulated.simulated_current_weather(site.lat, site.lon),
        ),
        _run_source(
            db, SOURCE_FORECAST, site.id, client is not None,
            lambda: cleaning.clean_forecast(client.forecast(site.lat, site.lon)),
            lambda: simulated.simulated_forecast(site.lat, site.lon),
        ),
    ]


def refresh_traffic(db: Session, site: Site, session=None) -> dict:
    client = TomTomClient(settings.tomtom_api_key, session) if settings.has_tomtom else None
    return _run_source(
        db, SOURCE_TRAFFIC, site.id, client is not None,
        lambda: cleaning.clean_traffic(client.flow(site.lat, site.lon)),
        lambda: simulated.simulated_traffic(site.lat, site.lon),
    )


def refresh_macro(db: Session, session=None) -> dict:
    client = BcrpClient(session)

    def fetch():
        fx = cleaning.clean_bcrp_series(client.fx_last_days())
        food = cleaning.clean_bcrp_series(client.food_cpi_last_months())
        return cleaning.summarize_macro(fx, food)

    return _run_source(db, SOURCE_MACRO, None, True, fetch, simulated.simulated_macro)


def refresh_site(db: Session, site: Site, session=None, include_macro: bool = True) -> list[dict]:
    results = refresh_weather(db, site, session) + [refresh_traffic(db, site, session)]
    if include_macro and latest(db, SOURCE_MACRO, None) is None:
        results.append(refresh_macro(db, session))
    return results


def purge_old(db: Session) -> int:
    cutoff = utcnow() - timedelta(days=RETENTION_DAYS)
    result = db.execute(delete(Snapshot).where(Snapshot.fetched_at < cutoff))
    db.commit()
    return result.rowcount or 0


def source_status(db: Session, site_id: int) -> list[dict]:
    """Estado de frescura de cada fuente para mostrar en la interfaz."""
    now = utcnow()
    out = []
    for source in (SOURCE_WEATHER, SOURCE_FORECAST, SOURCE_TRAFFIC, SOURCE_MACRO):
        sid = None if source == SOURCE_MACRO else site_id
        snap = latest(db, source, sid)
        last_any = latest(db, source, sid, ok_only=False)
        age = int((now - snap.fetched_at).total_seconds() // 60) if snap else None
        out.append(
            {
                "source": source,
                "last_update": snap.fetched_at.replace(tzinfo=timezone.utc).isoformat() if snap else None,
                "age_minutes": age,
                "is_simulated": bool(snap.is_simulated) if snap else None,
                "is_stale": age is None or age > STALE_AFTER[source],
                "last_error": last_any.error if last_any is not None and not last_any.ok else None,
            }
        )
    return out


def keys_configured() -> dict:
    return {"openweather": settings.has_openweather, "tomtom": settings.has_tomtom, "bcrp": True}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
