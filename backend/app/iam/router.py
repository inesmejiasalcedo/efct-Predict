"""Endpoints de autenticacion. Responsable: Mariana.

HU: Como dueno de restaurante quiero registrarme e iniciar sesion de forma segura.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.iam import service
from app.iam.deps import get_current_user
from app.iam.models import User
from app.iam.security import create_access_token
from app.shared.db import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: str
    password: str
    restaurant_name: str


class LoginIn(BaseModel):
    email: str
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


class LanguageIn(BaseModel):
    language: str


def user_out(user: User) -> dict:
    return {"id": user.id, "email": user.email, "role": user.role, "language": user.language}


def token_out(user: User) -> dict:
    return {"access_token": create_access_token(user.id, user.role), "token_type": "bearer", "user": user_out(user)}


@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    user = service.register_owner(db, body.email, body.password, body.restaurant_name)
    return token_out(user)


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = service.authenticate(db, body.email, body.password)
    return token_out(user)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_out(user)


@router.post("/change-password")
def change_password(body: ChangePasswordIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service.change_password(db, user, body.current_password, body.new_password)
    return {"ok": True}


@router.put("/language")
def set_language(body: LanguageIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Guarda el idioma preferido (lo usa la traduccion de Aaron)."""
    if body.language in ("es", "en"):
        user.language = body.language
        db.commit()
    return user_out(user)
