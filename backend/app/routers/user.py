from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response, ErrorCode
from app.core.security import verify_password, hash_password
from app.auth.models import User

router = APIRouter(prefix="/users", tags=["users"])


# ── Schemas ──
class ProfileUpdate(BaseModel):
    display_name: str | None = Field(None, max_length=100)
    avatar_emoji: str | None = Field(None, max_length=10)
    avatar_url: str | None = Field(None, max_length=500)
    email: str | None = Field(None, max_length=200)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=100)


# ── Endpoints ──
@router.get("/me")
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user["user_id"]))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "用户未找到"})
    return success_response(data={
        "user_id": str(u.id),
        "username": u.username,
        "display_name": u.display_name,
        "avatar_emoji": u.avatar_emoji or "",
        "avatar_url": u.avatar_url or "",
        "email": u.email or "",
        "role": u.role,
        "tenant_id": u.tenant_id,
        "idh_id": u.idh_id,
    })


@router.put("/me")
async def update_profile(
    body: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user["user_id"]))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "用户未找到"})

    if body.display_name is not None:
        u.display_name = body.display_name
    if body.avatar_emoji is not None:
        u.avatar_emoji = body.avatar_emoji
    if body.avatar_url is not None:
        u.avatar_url = body.avatar_url
    if body.email is not None:
        u.email = body.email

    await db.commit()
    await db.refresh(u)
    return success_response(data={
        "user_id": str(u.id),
        "username": u.username,
        "display_name": u.display_name,
        "avatar_emoji": u.avatar_emoji or "",
        "avatar_url": u.avatar_url or "",
        "email": u.email or "",
        "role": u.role,
        "tenant_id": u.tenant_id,
    })


@router.put("/me/password")
async def change_password(
    body: PasswordChange,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == user["user_id"]))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "用户未找到"})

    if not verify_password(body.current_password, u.password_hash):
        raise HTTPException(400, detail={"code": ErrorCode.BAD_REQUEST, "message": "当前密码不正确"})

    u.password_hash = hash_password(body.new_password)
    await db.commit()
    return success_response(data={"message": "密码已修改"})