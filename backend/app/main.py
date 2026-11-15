"""Punto de entrada del backend EFCT Predict.

Correr en local:   uvicorn app.main:app --reload
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.business.router import router as business_router
from app.config import settings
from app.iam.admin_router import router as admin_router
from app.iam.router import router as auth_router
from app.iam.service import ensure_admin
from app.ingestion import scheduler
from app.ingestion.router import router as data_router
from app.ingestion.service import keys_configured
from app.reporting.router import router as dashboard_router
from app.shared.db import SessionLocal, init_db

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("efct")

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        ensure_admin(db)
    if settings.secret_key_is_temporary:
        log.warning("SECRET_KEY no definido en .env: se uso uno temporal (las sesiones se pierden al reiniciar).")
    keys = keys_configured()
    log.info("API keys -> OpenWeather: %s | TomTom: %s | BCRP: publica", keys["openweather"], keys["tomtom"])
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="EFCT Predict API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth_router, admin_router, business_router, data_router, dashboard_router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok", "keys": keys_configured(), "env": settings.app_env}


# En produccion (nube) el backend tambien sirve el frontend compilado (frontend/dist)
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
