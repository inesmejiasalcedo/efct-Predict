"""Logica de registro, login y cambio de contrasena. Responsable: Mariana."""
from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.business.models import Restaurant
from app.config import settings
from app.iam.models import ROLE_ADMIN, ROLE_OWNER, User
from app.iam.security import (
    LOCK_MINUTES,
    MAX_FAILED_ATTEMPTS,
    hash_password,
    is_valid_email,
    password_problems,
    verify_password,
)
from app.shared.db import utcnow


def _bad_request(code: str, extra: list[str] | None = None):
    detail = code if not extra else {"code": code, "problems": extra}
    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=detail)


def register_owner(db: Session, email: str, password: str, restaurant_name: str) -> User:
    email = (email or "").strip().lower()
    if not is_valid_email(email):
        _bad_request("invalid_email")
    problems = password_problems(password)
    if problems:
        _bad_request("weak_password", problems)
    if not restaurant_name or not restaurant_name.strip():
        _bad_request("restaurant_name_required")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="email_taken")

    user = User(email=email, password_hash=hash_password(password), role=ROLE_OWNER)
    db.add(user)
    db.flush()
    db.add(Restaurant(owner_id=user.id, name=restaurant_name.strip()))
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    """Valida credenciales con bloqueo temporal tras varios intentos fallidos."""
    email = (email or "").strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    now = utcnow()

    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")
    if user.locked_until and user.locked_until > now:
        raise HTTPException(status.HTTP_423_LOCKED, detail="account_locked")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="account_disabled")

    if not verify_password(password, user.password_hash):
        user.failed_attempts = (user.failed_attempts or 0) + 1
        if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
            user.failed_attempts = 0
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    db.commit()
    return user


def change_password(db: Session, user: User, current: str, new: str) -> None:
    if not verify_password(current, user.password_hash):
        _bad_request("wrong_current_password")
    problems = password_problems(new)
    if problems:
        _bad_request("weak_password", problems)
    if current == new:
        _bad_request("password_unchanged")
    user.password_hash = hash_password(new)
    db.commit()


def ensure_admin(db: Session) -> None:
    """Crea el administrador definido en .env (ADMIN_EMAIL / ADMIN_PASSWORD) si no existe."""
    email = settings.admin_email.strip().lower()
    if not email or not settings.admin_password:
        return
    if password_problems(settings.admin_password) or not is_valid_email(email):
        print("[EFCT] ADMIN_EMAIL o ADMIN_PASSWORD no cumplen la politica; admin no creado.")
        return
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        db.add(User(email=email, password_hash=hash_password(settings.admin_password), role=ROLE_ADMIN))
        db.commit()
        print(f"[EFCT] Administrador creado: {email}")
    elif user.role != ROLE_ADMIN:
        user.role = ROLE_ADMIN
        db.commit()
