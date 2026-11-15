"""Pruebas de autenticacion (Mariana)."""
from tests.conftest import register


def test_register_and_me(client):
    headers = register(client)
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "dueno@test.pe"
    assert r.json()["role"] == "owner"


def test_password_is_hashed_not_stored(client):
    register(client)
    from app.iam.models import User
    from app.shared.db import SessionLocal

    with SessionLocal() as db:
        user = db.query(User).filter_by(email="dueno@test.pe").one()
        assert user.password_hash != "Clave2026"
        assert user.password_hash.startswith("$2")  # formato bcrypt


def test_weak_password_rejected(client):
    r = client.post("/api/auth/register", json={"email": "a@b.pe", "password": "123", "restaurant_name": "X"})
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "weak_password"
    assert "password_too_short" in r.json()["detail"]["problems"]


def test_duplicate_email(client):
    register(client)
    r = client.post("/api/auth/register", json={"email": "DUENO@test.pe", "password": "Clave2026", "restaurant_name": "Y"})
    assert r.status_code == 409


def test_login_and_wrong_password(client):
    register(client)
    assert client.post("/api/auth/login", json={"email": "dueno@test.pe", "password": "Clave2026"}).status_code == 200
    r = client.post("/api/auth/login", json={"email": "dueno@test.pe", "password": "Incorrecta1"})
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid_credentials"


def test_account_locks_after_5_failed_attempts(client):
    register(client)
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "dueno@test.pe", "password": "Incorrecta1"})
    r = client.post("/api/auth/login", json={"email": "dueno@test.pe", "password": "Clave2026"})
    assert r.status_code == 423
    assert r.json()["detail"] == "account_locked"


def test_protected_endpoint_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    bad = {"Authorization": "Bearer token-falso"}
    assert client.get("/api/auth/me", headers=bad).status_code == 401


def test_change_password(client):
    headers = register(client)
    r = client.post("/api/auth/change-password", headers=headers, json={"current_password": "Clave2026", "new_password": "NuevaClave9"})
    assert r.status_code == 200
    assert client.post("/api/auth/login", json={"email": "dueno@test.pe", "password": "NuevaClave9"}).status_code == 200
    assert client.post("/api/auth/login", json={"email": "dueno@test.pe", "password": "Clave2026"}).status_code == 401


def test_owner_cannot_use_admin(client):
    headers = register(client)
    assert client.get("/api/admin/restaurants", headers=headers).status_code == 403
