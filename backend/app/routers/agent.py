import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response, ErrorCode
from app.schemas.agent import AgentCreate, AgentUpdate, SkillCreate, SkillUpdate
from app.services import agent as srv
from app.models.agent import AgentSkill

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("")
async def create_agent(body: AgentCreate, db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    agent = await srv.create_agent(db, body, user["tenant_id"], user["user_id"])
    await db.commit()
    return success_response(data=_agent_to_dict(agent))


@router.get("")
async def list_agents(db: AsyncSession = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    agents = await srv.list_agents(db, user["tenant_id"])
    return success_response(data=[_agent_to_dict(a) for a in agents])


@router.get("/{agent_id}")
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db),
                    user: dict = Depends(get_current_user)):
    agent = await srv.get_agent(db, agent_id, user["tenant_id"])
    if not agent:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Agent not found"})
    return success_response(data=_agent_to_dict(agent, include_skills=True))


@router.put("/{agent_id}")
async def update_agent(agent_id: str, body: AgentUpdate, db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    agent = await srv.get_agent(db, agent_id, user["tenant_id"])
    if not agent:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Agent not found"})
    agent = await srv.update_agent(db, agent, body)
    await db.commit()
    return success_response(data=_agent_to_dict(agent, include_skills=True))


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    agent = await srv.get_agent(db, agent_id, user["tenant_id"])
    if not agent:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Agent not found"})
    await srv.delete_agent(db, agent)
    await db.commit()
    return success_response(message="Agent deleted")


# ── Skills ──

@router.get("/{agent_id}/skills")
async def list_skills(agent_id: str, db: AsyncSession = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    agent = await srv.get_agent(db, agent_id, user["tenant_id"])
    if not agent:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Agent not found"})
    skills = await srv.get_agent_skills(db, agent_id)
    return success_response(data=[_skill_to_dict(s) for s in skills])


@router.post("/{agent_id}/skills")
async def add_skill(agent_id: str, body: SkillCreate, db: AsyncSession = Depends(get_db),
                    user: dict = Depends(get_current_user)):
    agent = await srv.get_agent(db, agent_id, user["tenant_id"])
    if not agent:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Agent not found"})
    skill = await srv.add_skill(db, agent_id, body, user["tenant_id"])
    await db.commit()
    return success_response(data=_skill_to_dict(skill))


@router.put("/{agent_id}/skills/{skill_id}")
async def update_skill(agent_id: str, skill_id: str, body: SkillUpdate,
                       db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    # Verify agent ownership
    agent = await srv.get_agent(db, agent_id, user["tenant_id"])
    if not agent:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Agent not found"})
    # Find skill
    from sqlalchemy import select as sa_select
    result = await db.execute(
        sa_select(AgentSkill).where(AgentSkill.id == skill_id, AgentSkill.agent_id == agent_id)
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Skill not found"})
    skill = await srv.update_skill(db, skill, body)
    await db.commit()
    return success_response(data=_skill_to_dict(skill))


@router.delete("/{agent_id}/skills/{skill_id}")
async def delete_skill(agent_id: str, skill_id: str, db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    from sqlalchemy import select as sa_select
    skill = (await db.execute(
        sa_select(AgentSkill).where(AgentSkill.id == skill_id, AgentSkill.agent_id == agent_id)
    )).scalar_one_or_none()
    if not skill:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Skill not found"})
    await srv.delete_skill(db, skill)
    await db.commit()
    return success_response(message="Skill deleted")


def _agent_to_dict(a, include_skills=False) -> dict:
    d = {
        "id": a.id, "name": a.name, "display_name": a.display_name,
        "avatar_emoji": a.avatar_emoji, "role_description": a.role_description,
        "system_prompt": a.system_prompt,
        "provider": a.provider, "api_base": a.api_base,
        "api_key": _mask_key(a.api_key) if a.api_key else "",
        "agent_model": a.agent_model,
        "is_active": a.is_active, "user_id": a.user_id,
        "tenant_id": a.tenant_id, "created_by": a.created_by,
        "created_at": str(a.created_at) if a.created_at else None,
    }
    if include_skills:
        d["skills"] = [_skill_to_dict(s) for s in (a.skills or [])]
    return d


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def _skill_to_dict(s) -> dict:
    return {
        "id": s.id, "name": s.name, "description": s.description,
        "trigger_keywords": s.trigger_keywords, "action_type": s.action_type,
        "skill_prompt": s.skill_prompt, "data_config": s.data_config,
    }