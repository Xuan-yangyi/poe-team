from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.models import User
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.response import ErrorCode
from app.config import get_settings


class AuthError(Exception):
    def __init__(self, code: ErrorCode, message: str):
        self.code = code
        self.message = message


async def authenticate(db: AsyncSession, username: str, password: str) -> User:
    """Authenticate a user against the database."""
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise AuthError(ErrorCode.UNAUTHORIZED, "用户名或密码错误")
    if not user.is_active:
        raise AuthError(ErrorCode.UNAUTHORIZED, "账户已禁用")
    if not verify_password(password, user.password_hash):
        raise AuthError(ErrorCode.UNAUTHORIZED, "用户名或密码错误")

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    return user


def create_tokens_for_user(user: User) -> dict:
    """Create access + refresh tokens for an authenticated user."""
    settings = get_settings()
    user_id_str = str(user.id)
    claims = {"role": user.role, "tenant_id": user.tenant_id}
    if user.idh_id:
        claims["idh_id"] = user.idh_id
    access_token = create_access_token(user_id_str, extra_claims=claims)
    refresh_token = create_refresh_token(user_id_str)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }