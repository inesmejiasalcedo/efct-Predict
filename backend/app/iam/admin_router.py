"""Panel de administracion. Responsable: Aaron.

HU: Como administrador de EFCT quiero ver los restaurantes registrados con sus sedes,
ubicaciones, aforo y precios, y activar o desactivar cuentas, sin ver datos confidenciales.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.business.models import MenuItem, Restaurant, Site
from app.business.service import price_stats, site_out
from app.iam.deps import require_admin
from app.iam.models import ROLE_ADMIN, ROLE_OWNER, User
from app.ingestion.models import Snapshot
from app.shared.db import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])


def mask_email(email: str) -> str:
    """juan.perez@gmail.com -> ju*******@gmail.com (no exponemos datos personales)."""
    local, _, domain = email.partition("@")
    visible = local[:2]
    return f"{visible}{'*' * max(len(local) - 2, 3)}@{domain}"


class UserPatch(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None


@router.get("/stats")
def stats(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    last = db.scalar(select(func.max(Snapshot.fetched_at)))
    return {
        "restaurants": db.scalar(select(func.count(Restaurant.id))) or 0,
        "sites": db.scalar(select(func.count(Site.id))) or 0,
        "menu_items": db.scalar(select(func.count(MenuItem.id))) or 0,
        "users": db.scalar(select(func.count(User.id))) or 0,
        "last_data_update": last.isoformat() + "Z" if last else None,
    }


@router.get("/restaurants")
def restaurants(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(Restaurant).order_by(Restaurant.created_at.desc())).all()
    out = []
    for r in rows:
        owner = db.get(User, r.owner_id)
        out.append(
            {
                "id": r.id,
                "name": r.name,
                "category": r.category,
                "description": r.description,
                "created_at": r.created_at.isoformat() + "Z",
                "is_active": bool(owner and owner.is_active),
                "owner_user_id": r.owner_id,
                "sites": [site_out(s) for s in r.sites],
                "total_capacity": sum(s.capacity for s in r.sites),
                "menu": [{"name": m.name, "price": m.price, "category": m.category} for m in r.menu_items],
                "menu_stats": price_stats(r.menu_items),
            }
        )
    return out


@router.get("/users")
def users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.scalars(select(User).order_by(User.created_at.desc())).all()
    restaurants_by_owner = {r.owner_id: r.name for r in db.scalars(select(Restaurant)).all()}
    return [
        {
            "id": u.id,
            "email": mask_email(u.email),
            "role": u.role,
            "is_active": u.is_active,
            "restaurant": restaurants_by_owner.get(u.id),
            "created_at": u.created_at.isoformat() + "Z",
            "last_login_at": u.last_login_at.isoformat() + "Z" if u.last_login_at else None,
        }
        for u in rows
    ]


@router.patch("/users/{user_id}")
def patch_user(user_id: int, body: UserPatch, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user_not_found")
    if user.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="cannot_modify_self")
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.role is not None:
        if body.role not in (ROLE_OWNER, ROLE_ADMIN):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_role")
        user.role = body.role
    db.commit()
    return {"id": user.id, "is_active": user.is_active, "role": user.role}
