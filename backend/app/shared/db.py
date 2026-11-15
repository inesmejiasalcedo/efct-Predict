"""Conexion a base de datos. SQLite en local, Postgres en la nube (solo cambia DATABASE_URL)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _make_engine(url: str):
    if url.startswith("postgres://"):  # formato que usan algunos proveedores cloud
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("sqlite:///./"):  # ruta relativa -> siempre dentro de backend/
        from app.config import BASE_DIR

        url = f"sqlite:///{(BASE_DIR / url[len('sqlite:///./'):]).as_posix()}"
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Importar modelos para que se registren en Base.metadata
    from app.iam import models as _iam  # noqa: F401
    from app.business import models as _business  # noqa: F401
    from app.ingestion import models as _ingestion  # noqa: F401

    Base.metadata.create_all(bind=engine)
