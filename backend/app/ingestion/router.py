"""Endpoints del pipeline de datos. Responsable: Harry.

HU: Como gerente quiero que los datos externos se actualicen solos y poder ver cuando fue
la ultima actualizacion y de que fuente viene cada dato.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.business.service import get_site_for_user
from app.iam.deps import get_current_user
from app.iam.models import User
from app.ingestion import service
from app.ingestion.models import SOURCE_FORECAST, SOURCE_MACRO, SOURCE_TRAFFIC, SOURCE_WEATHER
from app.shared.db import get_db

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/status")
def status(site_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_site_for_user(db, user, site_id)
    return {"keys": service.keys_configured(), "sources": service.source_status(db, site_id)}


@router.post("/refresh")
def refresh(site_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    site = get_site_for_user(db, user, site_id)
    results = service.refresh_site(db, site, include_macro=False)
    results.append(service.refresh_macro(db))
    return {"results": results, "sources": service.source_status(db, site_id)}


@router.get("/external")
def external(site_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Ultimos datos externos ya limpios para la sede (para las paginas de detalle)."""
    get_site_for_user(db, user, site_id)

    def payload(source, sid):
        snap = service.latest(db, source, sid)
        return {"data": snap.payload, "simulated": snap.is_simulated} if snap else None

    return {
        "weather": payload(SOURCE_WEATHER, site_id),
        "forecast": payload(SOURCE_FORECAST, site_id),
        "traffic": payload(SOURCE_TRAFFIC, site_id),
        "macro": payload(SOURCE_MACRO, None),
    }
