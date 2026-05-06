from __future__ import annotations

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_refresh_token,
    verify_password,
)
from app.repositories.auth_session_repository import AuthSessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthTokenResponse, AuthUserResponse, CompanySummary


class AuthService:
    def __init__(self) -> None:
        self.user_repository = UserRepository()
        self.session_repository = AuthSessionRepository()

    def login(self, *, email: str, password: str) -> AuthTokenResponse:
        user = self.user_repository.get_user_by_email(email)
        if user is None or not verify_password(password, user["password_hash"]):
            raise AuthenticationError("Email ou senha invalidos.")
        if not user["is_active"]:
            raise AuthenticationError("Usuario inativo.")

        refresh_token, session_id, expires_at = create_refresh_token(
            user_id=user["id"],
            company_id=user["company_id"],
            role=user["role"],
        )
        self.session_repository.create_session(
            session_id=session_id,
            user_id=user["id"],
            refresh_token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )
        self.user_repository.touch_last_login(user["id"])

        return AuthTokenResponse(
            access_token=create_access_token(
                user_id=user["id"],
                company_id=user["company_id"],
                role=user["role"],
            ),
            refresh_token=refresh_token,
            user=self._build_user_response(user),
        )

    def refresh(self, refresh_token: str) -> AuthTokenResponse:
        payload = decode_token(refresh_token, expected_type="refresh")
        session_id = str(payload["sid"])
        user_id = str(payload["sub"])
        session = self.session_repository.get_session(session_id)
        if session["user_id"] != user_id:
            raise AuthenticationError("Sessao invalida.")
        if session["revoked_at"] is not None:
            raise AuthenticationError("Sessao encerrada.")
        if session["refresh_token_hash"] != hash_refresh_token(refresh_token):
            raise AuthenticationError("Refresh token invalido.")

        user = self.user_repository.get_user_by_id(user_id)
        if not user["is_active"]:
            raise AuthenticationError("Usuario inativo.")

        new_refresh_token, _, expires_at = create_refresh_token(
            user_id=user["id"],
            company_id=user["company_id"],
            role=user["role"],
            session_id=session_id,
        )
        self.session_repository.rotate_session(
            session_id=session_id,
            refresh_token_hash=hash_refresh_token(new_refresh_token),
            expires_at=expires_at,
        )
        return AuthTokenResponse(
            access_token=create_access_token(
                user_id=user["id"],
                company_id=user["company_id"],
                role=user["role"],
            ),
            refresh_token=new_refresh_token,
            user=self._build_user_response(user),
        )

    def logout(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token, expected_type="refresh")
        session_id = str(payload["sid"])
        self.session_repository.revoke_session(session_id)

    def authenticate_access_token(self, token: str) -> dict:
        payload = decode_token(token, expected_type="access")
        user = self.user_repository.get_user_by_id(str(payload["sub"]))
        if not user["is_active"]:
            raise AuthenticationError("Usuario inativo.")
        return user

    def build_me(self, user: dict) -> AuthUserResponse:
        return self._build_user_response(user)

    def _build_user_response(self, user: dict) -> AuthUserResponse:
        return AuthUserResponse(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            role=user["role"],
            is_active=bool(user["is_active"]),
            company=CompanySummary(
                id=user["company_id"],
                name=user["company_name"],
            ),
        )


auth_service = AuthService()
