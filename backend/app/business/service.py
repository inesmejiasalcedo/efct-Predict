"""Reglas del negocio para restaurante, sedes y menu. Responsable: Matias."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.business.models import MenuItem, Restaurant, Site
from app.iam.models import ROLE_ADMIN, User


def _bad(code: str):
    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=code)


def get_restaurant(db: Session, user: User) -> Restaurant:
    restaurant = db.scalar(select(Restaurant).where(Restaurant.owner_id == user.id))
    if restaurant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="restaurant_not_found")
    return restaurant


def get_site_for_user(db: Session, user: User, site_id: int) -> Site:
    """Una sede solo la ve su dueno (o un admin)."""
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="site_not_found")
    if user.role != ROLE_ADMIN and site.restaurant.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="site_not_found")
    return site


# ---------- Restaurante ----------

def update_restaurant(db: Session, restaurant: Restaurant, data: dict) -> Restaurant:
    name = (data.get("name") or "").strip()
    if not name:
        _bad("restaurant_name_required")
    restaurant.name = name[:120]
    restaurant.category = (data.get("category") or "").strip()[:80] or None
    restaurant.description = (data.get("description") or "").strip()[:500] or None
    db.commit()
    return restaurant


# ---------- Sedes ----------

def validate_site(data: dict) -> dict:
    name = (data.get("name") or "").strip()
    if not name:
        _bad("site_name_required")
    try:
        lat, lon = float(data.get("lat")), float(data.get("lon"))
    except (TypeError, ValueError):
        _bad("invalid_location")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        _bad("invalid_location")
    try:
        capacity = int(data.get("capacity"))
    except (TypeError, ValueError):
        _bad("invalid_capacity")
    if not 1 <= capacity <= 5000:
        _bad("invalid_capacity")
    open_hour = int(data.get("open_hour", 12))
    close_hour = int(data.get("close_hour", 23))
    if not (0 <= open_hour <= 23 and 1 <= close_hour <= 24 and open_hour < close_hour):
        _bad("invalid_hours")
    return {
        "name": name[:120],
        "address": (data.get("address") or "").strip()[:255] or None,
        "district": (data.get("district") or "").strip()[:80] or None,
        "lat": round(lat, 6),
        "lon": round(lon, 6),
        "capacity": capacity,
        "open_hour": open_hour,
        "close_hour": close_hour,
    }


def create_site(db: Session, restaurant: Restaurant, data: dict) -> Site:
    site = Site(restaurant_id=restaurant.id, **validate_site(data))
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


def update_site(db: Session, site: Site, data: dict) -> Site:
    for key, value in validate_site(data).items():
        setattr(site, key, value)
    db.commit()
    return site


def delete_site(db: Session, site: Site) -> None:
    db.delete(site)
    db.commit()


# ---------- Menu ----------

def validate_menu_item(data: dict) -> dict:
    name = (data.get("name") or "").strip()
    if not name:
        _bad("menu_name_required")
    try:
        price = float(data.get("price"))
    except (TypeError, ValueError):
        _bad("invalid_price")
    if not 0 < price <= 10000:
        _bad("invalid_price")
    return {
        "name": name[:120],
        "price": round(price, 2),
        "description": (data.get("description") or "").strip()[:500] or None,
        "category": (data.get("category") or "").strip()[:60] or None,
    }


def create_menu_item(db: Session, restaurant: Restaurant, data: dict) -> MenuItem:
    item = MenuItem(restaurant_id=restaurant.id, **validate_menu_item(data))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_menu_item(db: Session, restaurant: Restaurant, item_id: int) -> MenuItem:
    item = db.get(MenuItem, item_id)
    if item is None or item.restaurant_id != restaurant.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="menu_item_not_found")
    return item


def price_stats(items: list[MenuItem]) -> dict:
    prices = [i.price for i in items]
    if not prices:
        return {"count": 0, "avg": None, "min": None, "max": None}
    return {
        "count": len(prices),
        "avg": round(sum(prices) / len(prices), 2),
        "min": min(prices),
        "max": max(prices),
    }


# ---------- Serializacion ----------

def site_out(site: Site) -> dict:
    return {
        "id": site.id,
        "name": site.name,
        "address": site.address,
        "district": site.district,
        "lat": site.lat,
        "lon": site.lon,
        "capacity": site.capacity,
        "open_hour": site.open_hour,
        "close_hour": site.close_hour,
        "is_active": site.is_active,
    }


def menu_out(item: MenuItem) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "price": item.price,
        "description": item.description,
        "category": item.category,
    }


def restaurant_out(r: Restaurant) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "category": r.category,
        "description": r.description,
        "sites": [site_out(s) for s in r.sites],
        "menu_stats": price_stats(r.menu_items),
    }
