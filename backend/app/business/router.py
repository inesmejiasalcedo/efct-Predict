"""Endpoints de personalizacion del negocio. Responsable: Matias.

HU: Como dueno quiero registrar mis sedes (ubicacion y aforo) y mi menu (item, precio,
descripcion opcional) para que las predicciones se ajusten a mi negocio.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.business import service
from app.business.districts import DISTRICTS
from app.iam.deps import get_current_user
from app.iam.models import User
from app.shared.db import get_db

router = APIRouter(prefix="/api/business", tags=["business"])


class RestaurantIn(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None


class SiteIn(BaseModel):
    name: str
    address: Optional[str] = None
    district: Optional[str] = None
    lat: float
    lon: float
    capacity: int
    open_hour: int = 12
    close_hour: int = 23


class MenuItemIn(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    category: Optional[str] = None


@router.get("/districts")
def districts():
    return DISTRICTS


@router.get("/restaurant")
def get_restaurant(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.restaurant_out(service.get_restaurant(db, user))


@router.put("/restaurant")
def update_restaurant(body: RestaurantIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    restaurant = service.get_restaurant(db, user)
    return service.restaurant_out(service.update_restaurant(db, restaurant, body.model_dump()))


@router.get("/sites")
def list_sites(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [service.site_out(s) for s in service.get_restaurant(db, user).sites]


@router.post("/sites", status_code=201)
def create_site(body: SiteIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    restaurant = service.get_restaurant(db, user)
    site = service.create_site(db, restaurant, body.model_dump())
    # Traer datos externos para la nueva sede en segundo plano
    from app.ingestion.scheduler import refresh_site_async

    refresh_site_async(site.id)
    return service.site_out(site)


@router.put("/sites/{site_id}")
def update_site(site_id: int, body: SiteIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    site = service.get_site_for_user(db, user, site_id)
    return service.site_out(service.update_site(db, site, body.model_dump()))


@router.delete("/sites/{site_id}", status_code=204)
def delete_site(site_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service.delete_site(db, service.get_site_for_user(db, user, site_id))


@router.get("/menu")
def list_menu(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    restaurant = service.get_restaurant(db, user)
    items = sorted(restaurant.menu_items, key=lambda i: (i.category or "", i.name))
    return {"items": [service.menu_out(i) for i in items], "stats": service.price_stats(restaurant.menu_items)}


@router.post("/menu", status_code=201)
def create_menu_item(body: MenuItemIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    restaurant = service.get_restaurant(db, user)
    return service.menu_out(service.create_menu_item(db, restaurant, body.model_dump()))


@router.put("/menu/{item_id}")
def update_menu_item(item_id: int, body: MenuItemIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    restaurant = service.get_restaurant(db, user)
    item = service.get_menu_item(db, restaurant, item_id)
    for key, value in service.validate_menu_item(body.model_dump()).items():
        setattr(item, key, value)
    db.commit()
    return service.menu_out(item)


@router.delete("/menu/{item_id}", status_code=204)
def delete_menu_item(item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    restaurant = service.get_restaurant(db, user)
    db.delete(service.get_menu_item(db, restaurant, item_id))
    db.commit()
