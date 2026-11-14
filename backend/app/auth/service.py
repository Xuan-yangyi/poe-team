from app.auth.models import USERS
from app.core.security import verify_password, create_access_token, create_refresh_token, hash_password
from app.core.response import ErrorCode
from app.config import get_settings


class AuthError(Exception):
    def __init__(self, code: ErrorCode, message: str):
        self.code = code
        self.message = message


def authenticate(username: str, password: str) -> dict:
    user = USERS.get(username)
    if not user:
        raise AuthError(ErrorCode.UNAUTHORIZED, "用户名或密码错误")
    if not verify_password(password, user["password_hash"]):
        raise AuthError(ErrorCode.UNAUTHORIZED, "用户名或密码错误")
    return user


def create_tokens(user: dict) -> dict:
    settings = get_settings()
    claims = {"role": user["role"], "tenant_id": user["tenant_id"]}
    if "idh_id" in user:
        claims["idh_id"] = user["idh_id"]
    access_token = create_access_token(user["id"], extra_claims=claims)
    refresh_token = create_refresh_token(user["id"])
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }