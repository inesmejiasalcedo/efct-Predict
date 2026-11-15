"""Refresco automatico de datos externos. Responsable: Harry.

Usa APScheduler dentro del mismo proceso del backend:
  - clima y pronostico: cada WEATHER_REFRESH_MINUTES (30 por defecto)
  - trafico: cada TRAFFIC_REFRESH_MINUTES (15 por defecto)
  - BCRP: cada MACRO_REFRESH_MINUTES (12 horas por defecto)
"""
from __future__ import annotations

import logging
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.business.models import Site
from app.config import settings
from app.ingestion import service
from app.shared.db import SessionLocal

log = logging.getLogger("efct.scheduler")
_scheduler: BackgroundScheduler | None = None
_lock = threading.Lock()


def _active_sites(db):
    return db.scalars(select(Site).where(Site.is_active.is_(True))).all()


def job_weather() -> None:
    with _lock, SessionLocal() as db:
        for site in _active_sites(db):
            service.refresh_weather(db, site)


def job_traffic() -> None:
    with _lock, SessionLocal() as db:
        for site in _active_sites(db):
            service.refresh_traffic(db, site)


def job_macro() -> None:
    with _lock, SessionLocal() as db:
        service.refresh_macro(db)
        service.purge_old(db)


def refresh_all_now() -> None:
    job_macro()
    job_weather()
    job_traffic()


def refresh_site_async(site_id: int) -> None:
    """Refresca una sede en segundo plano (ej. al crearla) sin bloquear la respuesta."""
    if not settings.scheduler_enabled:
        return

    def run():
        try:
            with _lock, SessionLocal() as db:
                site = db.get(Site, site_id)
                if site:
                    service.refresh_site(db, site)
        except Exception:  # noqa: BLE001
            log.exception("refresh_site_async failed")

    threading.Thread(target=run, daemon=True).start()


def start() -> None:
    global _scheduler
    if not settings.scheduler_enabled or _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(job_weather, "interval", minutes=settings.weather_refresh_min, id="weather")
    _scheduler.add_job(job_traffic, "interval", minutes=settings.traffic_refresh_min, id="traffic")
    _scheduler.add_job(job_macro, "interval", minutes=settings.macro_refresh_min, id="macro")
    _scheduler.start()
    # Primera carga al arrancar, en segundo plano
    threading.Thread(target=refresh_all_now, daemon=True).start()
    log.info("Scheduler iniciado")


def shutdown() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
