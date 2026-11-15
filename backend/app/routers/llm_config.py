from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response, ErrorCode
from app.schemas.llm_config import (
    LLMConfigCreate, LLMConfigUpdate, LLMConfigTest, PROVIDER_PRESETS,
)
from app.services import llm_config as srv

router = APIRouter(prefix="/llm-config", tags=["llm-config"])


@router.get("/presets")
async def get_presets():
    """Return available provider presets so the frontend can prefill fields."""
    return success_response(data=[
        {"key": k, "label": v["label"], "api_base": v["api_base"], "model": v["model"]}
        for k, v in PROVIDER_PRESETS.items()
    ])


@router.get("")
async def list_configs(db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    configs = await srv.list_configs(db, user["tenant_id"])
    return success_response(data=[_cfg_to_dict(c) for c in configs])


@router.post("")
async def create_config(body: LLMConfigCreate, db: AsyncSession = Depends(get_db),
                        user: dict = Depends(get_current_user)):
    cfg = await srv.create_config(db, body, user["tenant_id"])
    await db.commit()
    return success_response(data=_cfg_to_dict(cfg))


@router.put("/{config_id}")
async def update_config(config_id: str, body: LLMConfigUpdate,
                        db: AsyncSession = Depends(get_db),
                        user: dict = Depends(get_current_user)):
    from sqlalchemy import select
    from app.models.llm_config import LLMConfig
    cfg = (await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id, LLMConfig.tenant_id == user["tenant_id"])
    )).scalar_one_or_none()
    if not cfg:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Config not found"})
    cfg = await srv.update_config(db, cfg, body)
    await db.commit()
    return success_response(data=_cfg_to_dict(cfg))


@router.delete("/{config_id}")
async def delete_config(config_id: str, db: AsyncSession = Depends(get_db),
                        user: dict = Depends(get_current_user)):
    from sqlalchemy import select
    from app.models.llm_config import LLMConfig
    cfg = (await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id, LLMConfig.tenant_id == user["tenant_id"])
    )).scalar_one_or_none()
    if not cfg:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Config not found"})
    await srv.delete_config(db, cfg)
    await db.commit()
    return success_response(message="Config deleted")


@router.post("/{config_id}/test")
async def test_config(config_id: str, body: LLMConfigTest,
                      db: AsyncSession = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    from sqlalchemy import select
    from app.models.llm_config import LLMConfig
    cfg = (await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id, LLMConfig.tenant_id == user["tenant_id"])
    )).scalar_one_or_none()
    if not cfg:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Config not found"})
    result = await srv.test_connection(cfg, body.message)
    return success_response(data=result)


def _cfg_to_dict(cfg) -> dict:
    return {
        "id": cfg.id, "provider": cfg.provider,
        "api_base": cfg.api_base,
        "api_key": _mask_key(cfg.api_key),
        "model": cfg.model,
        "extra_params": cfg.extra_params,
        "is_active": cfg.is_active,
        "description": cfg.description,
        "created_at": str(cfg.created_at) if cfg.created_at else None,
    }


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]