"""Hash de contrasenas (bcrypt) y tokens JWT. Responsable: Mariana.

Nunca se guarda la contrasena: solo su hash bcrypt con sal aleatoria.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings

ALGORITHM = "HS256"
MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def password_problems(password: str) -> list[str]:
    """Devuelve codigos de error de la politica de contrasenas (lista vacia = valida)."""
    problems = []
    if len(password) < 8:
        problems.append("password_too_short")
    if len(password.encode("utf-8")) > 72:  # limite de bcrypt
        problems.append("password_too_long")
    if not re.search(r"[A-Za-z]", password):
        problems.append("password_needs_letter")
    if not re.search(r"\d", password):
        problems.append("password_needs_number")
    return problems


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or ""))


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.token_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Lanza jwt.PyJWTError si el token es invalido o expiro."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
