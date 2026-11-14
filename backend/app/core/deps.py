from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.security import decode_token
from app.core.response import ErrorCode

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail={
            "code": ErrorCode.UNAUTHORIZED, "message": "未提供认证令牌"
        })
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail={
            "code": ErrorCode.UNAUTHORIZED, "message": "令牌无效或已过期"
        })
    return {
        "user_id": payload["sub"],
        "role": payload.get("role", ""),
        "tenant_id": payload.get("tenant_id", ""),
        "idh_id": payload.get("idh_id"),
    }


async def require_role(role: str, user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != role and user["role"] != "factory_admin":
        raise HTTPException(status_code=403, detail={
            "code": ErrorCode.FORBIDDEN_ROLE, "message": f"需要 {role} 权限"
        })
    return user