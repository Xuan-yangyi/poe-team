from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response, ErrorCode
from app.schemas.conversation import ConversationCreate, GroupCreate, MessageCreate, TagCreate
from app.services import conversation as srv

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("")
async def create_conversation(body: ConversationCreate, db: AsyncSession = Depends(get_db),
                              user: dict = Depends(get_current_user)):
    conv = await srv.create_conversation(db, body, user["tenant_id"], user["user_id"])
    await db.commit()
    return success_response(data={"id": conv.id, "conv_type": conv.conv_type, "ref_id": conv.ref_id})


@router.get("")
async def list_conversations(conv_type: str | None = Query(None),
                             db: AsyncSession = Depends(get_db),
                             user: dict = Depends(get_current_user)):
    convs = await srv.list_conversations(db, user["tenant_id"], conv_type, user_id=user["user_id"])

    # Resolve member user_ids to display_names for each conversation
    from app.auth.models import User as UserModel
    all_user_ids = set()
    conv_member_map: dict[str, list[str]] = {}
    for c in convs:
        if c.conv_type in ("group", "direct"):
            mbrs = await srv.get_group_members(db, c.id)
            ids = [m.user_id for m in mbrs]
            conv_member_map[c.id] = ids
            all_user_ids.update(ids)

    user_map: dict[str, str] = {}
    if all_user_ids:
        result = await db.execute(
            select(UserModel).where(UserModel.id.in_(list(all_user_ids)))
        )
        for u in result.scalars().all():
            user_map[str(u.id)] = u.display_name or u.username

    return success_response(data=[{
        "id": c.id, "conv_type": c.conv_type, "ref_id": c.ref_id,
        "title": c.title, "is_active": c.is_active, "tenant_id": c.tenant_id,
        "last_msg_preview": c.last_msg_preview,
        "last_msg_at": c.last_msg_at.isoformat() if c.last_msg_at else None,
        "member_ids": conv_member_map.get(c.id, []),
        "member_names": [user_map.get(uid, uid) for uid in conv_member_map.get(c.id, [])],
    } for c in convs])


@router.get("/{conv_id}")
async def get_conversation(conv_id: str, db: AsyncSession = Depends(get_db),
                           user: dict = Depends(get_current_user)):
    conv = await srv.get_conversation(db, conv_id, user["tenant_id"])
    if not conv:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Conversation not found"})
    # Also fetch members for group conversations
    members = []
    if conv.conv_type == "group":
        mbrs = await srv.get_group_members(db, conv_id)
        members = [{"user_id": m.user_id, "tenant_id": m.tenant_id} for m in mbrs]
    return success_response(data={
        "id": conv.id, "conv_type": conv.conv_type, "ref_id": conv.ref_id,
        "title": conv.title, "is_active": conv.is_active, "members": members,
    })


@router.post("/group")
async def create_group(body: GroupCreate, db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    conv = await srv.create_group(db, body, user["tenant_id"], user["user_id"])
    await db.commit()
    return success_response(data={
        "id": conv.id, "conv_type": conv.conv_type, "title": conv.title,
    })


@router.post("/{conv_id}/messages")
async def post_message(conv_id: str, body: MessageCreate, db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    body.conversation_id = conv_id
    msg = await srv.post_message(db, body, user["tenant_id"], user["user_id"])
    await db.commit()

    # Fire background task for agent responses so the user gets instant feedback
    import asyncio
    from app.database import async_session_factory
    from app.services import agent as agent_srv
    from app.schemas.conversation import MessageCreate as Mc

    async def _process_agent_responses():
        try:
            async with async_session_factory() as bg_db:
                triggers = await agent_srv.check_agent_trigger(
                    bg_db, conv_id, body.content, user["user_id"], user["tenant_id"])
                for t in triggers:
                    ctx = await agent_srv.build_agent_context(
                        bg_db, t["agent"], t["skill"], conv_id, body.content)
                    response = await agent_srv.generate_agent_response(
                        bg_db, t["agent"], t["skill"], ctx, user.get("username", ""))
                    if response:
                        agent_msg = await srv.post_message(bg_db, Mc(
                            conversation_id=conv_id, content=response, msg_type="text",
                            parent_msg_id=msg.id,
                        ), user["tenant_id"], t["agent"].user_id or t["agent"].id)
                await bg_db.commit()
        except Exception as e:
            import traceback
            print(f"[agent response error] {traceback.format_exc()}")

    asyncio.create_task(_process_agent_responses())

    return success_response(data={
        "id": msg.id, "msg_type": msg.msg_type, "sender_id": msg.sender_id,
    })


@router.get("/{conv_id}/messages")
async def get_messages(conv_id: str, limit: int = Query(50, ge=1, le=200),
                       offset: int = Query(0, ge=0),
                       db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    msgs = await srv.get_messages(db, conv_id, user["tenant_id"], limit, offset)
    return success_response(data=[{
        "id": m.id, "sender_id": m.sender_id, "msg_type": m.msg_type,
        "content": m.content, "parent_msg_id": m.parent_msg_id, "created_at": m.created_at
    } for m in msgs])


@router.get("/{conv_id}/members")
async def get_members(conv_id: str, db: AsyncSession = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    """Get conversation members with display info (for @mentions)."""
    from app.auth.models import User as UserModel
    from app.models.agent import Agent as AgentModel

    mbrs = await srv.get_group_members(db, conv_id)
    user_ids = [m.user_id for m in mbrs]

    # Resolve users
    user_map: dict = {}
    if user_ids:
        result = await db.execute(select(UserModel).where(UserModel.id.in_(user_ids)))
        for u in result.scalars().all():
            user_map[str(u.id)] = u

    # Resolve agents (agent.user_id -> agent)
    agent_map: dict = {}
    if user_ids:
        result = await db.execute(
            select(AgentModel).where(AgentModel.user_id.in_(user_ids)))
        for a in result.scalars().all():
            agent_map[a.user_id] = a

    data = []
    for m in mbrs:
        u = user_map.get(m.user_id)
        a = agent_map.get(m.user_id)
        data.append({
            "user_id": m.user_id,
            "display_name": u.display_name if u else (a.display_name if a else m.user_id),
            "role": u.role if u else "agent",
            "agent_name": a.name if a else None,
            "mention_handle": f"@{a.name}" if a else f"@{u.username if u else m.user_id}",
        })

    return success_response(data=data)


@router.post("/{conv_id}/members")
async def add_member(conv_id: str, body: dict, db: AsyncSession = Depends(get_db),
                     user: dict = Depends(get_current_user)):
    """Add a member (user or agent) to a conversation."""
    member = await srv.add_member(db, conv_id, body["user_id"], user["tenant_id"])
    await db.commit()
    return success_response(data={"id": member.id, "user_id": member.user_id})


@router.post("/tags")
async def add_tag(body: TagCreate, db: AsyncSession = Depends(get_db),
                  user: dict = Depends(get_current_user)):
    tag = await srv.add_tag(db, body, user["tenant_id"], user["user_id"])
    await db.commit()
    return success_response(data={"id": tag.id, "tag_type": tag.tag_type, "tag_value": tag.tag_value})