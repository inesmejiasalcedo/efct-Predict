"""Pruebas de personalizacion del negocio (Matias) y administracion (Aaron)."""
from tests.conftest import SITE, admin_headers, register


def test_create_site_and_validate(client):
    h = register(client)
    r = client.post("/api/business/sites", headers=h, json=SITE)
    assert r.status_code == 201
    assert r.json()["capacity"] == 60

    bad = dict(SITE, capacity=0)
    assert client.post("/api/business/sites", headers=h, json=bad).json()["detail"] == "invalid_capacity"
    bad = dict(SITE, open_hour=23, close_hour=12)
    assert client.post("/api/business/sites", headers=h, json=bad).json()["detail"] == "invalid_hours"


def test_menu_items_with_optional_description(client):
    h = register(client)
    r1 = client.post("/api/business/menu", headers=h, json={"name": "Rocoto relleno", "price": 38})
    r2 = client.post("/api/business/menu", headers=h, json={"name": "Chupe", "price": 55, "description": "De camarones"})
    assert r1.status_code == r2.status_code == 201
    assert r1.json()["description"] is None
    menu = client.get("/api/business/menu", headers=h).json()
    assert menu["stats"] == {"count": 2, "avg": 46.5, "min": 38.0, "max": 55.0}
    assert client.post("/api/business/menu", headers=h, json={"name": "X", "price": -5}).status_code == 400


def test_owner_cannot_see_other_restaurant_site(client):
    h1 = register(client)
    site_id = client.post("/api/business/sites", headers=h1, json=SITE).json()["id"]
    h2 = register(client, email="otro@test.pe", name="Otro")
    assert client.get("/api/dashboard/summary", headers=h2, params={"site_id": site_id}).status_code == 404


def test_admin_sees_restaurants_without_personal_data(client):
    h = register(client)
    client.post("/api/business/sites", headers=h, json=SITE)
    client.post("/api/business/menu", headers=h, json={"name": "Adobo", "price": 35})
    ah = admin_headers(client)
    rows = client.get("/api/admin/restaurants", headers=ah).json()
    assert rows[0]["name"] == "13 Monjas"
    assert rows[0]["sites"][0]["district"] == "Cercado de Arequipa"
    assert rows[0]["menu_stats"]["avg"] == 35.0
    assert "email" not in rows[0]
    users = client.get("/api/admin/users", headers=ah).json()
    assert all("*" in u["email"] for u in users)


def test_admin_can_disable_account(client):
    register(client)
    ah = admin_headers(client)
    owner = next(u for u in client.get("/api/admin/users", headers=ah).json() if u["role"] == "owner")
    assert client.patch(f"/api/admin/users/{owner['id']}", headers=ah, json={"is_active": False}).status_code == 200
    r = client.post("/api/auth/login", json={"email": "dueno@test.pe", "password": "Clave2026"})
    assert r.status_code == 403
