from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Literal
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(
    *,
    user_id: str,
    company_id: str,
    role: str,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "company_id": company_id,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    *,
    user_id: str,
    company_id: str,
    role: str,
    session_id: str | None = None,
) -> tuple[str, str, datetime]:
    settings = get_settings()
    now = datetime.now(UTC)
    session_id = session_id or str(uuid4())
    expires_at = now + timedelta(days=settings.refresh_token_days)
    payload = {
        "sub": user_id,
        "company_id": company_id,
        "role": role,
        "type": "refresh",
        "sid": session_id,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, session_id, expires_at


def decode_token(token: str, *, expected_type: Literal["access", "refresh"]) -> dict[str, object]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Token invalido ou expirado.") from exc

    if payload.get("type") != expected_type:
        raise AuthenticationError("Tipo de token invalido.")
    return payload


def hash_refresh_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
