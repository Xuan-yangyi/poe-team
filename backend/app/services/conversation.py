import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, ConversationMember, Message, MsgTag
from app.schemas.conversation import ConversationCreate, GroupCreate, MessageCreate, TagCreate
from app.events.bus import emit_event


async def create_conversation(db: AsyncSession, data: ConversationCreate,
                              tenant_id: str, actor_id: str) -> Conversation:
    conv = Conversation(
        id=str(uuid.uuid4()),
        conv_type=data.conv_type,
        ref_id=data.ref_id,
        title=data.title,
        tenant_id=tenant_id,
    )
    db.add(conv)
    await emit_event(db, "CONV.CREATED", "conversation", conv.id,
                     {"conv_type": data.conv_type, "ref_id": data.ref_id}, actor_id, tenant_id)
    await db.flush()
    return conv


async def create_group(db: AsyncSession, data: GroupCreate,
                       tenant_id: str, actor_id: str) -> Conversation:
    """Create a group conversation and add all members."""
    conv = Conversation(
        id=str(uuid.uuid4()),
        conv_type="group",
        ref_id=str(uuid.uuid4()),
        title=data.title,
        tenant_id=tenant_id,
    )
    db.add(conv)
    await db.flush()

    # Add all members (including creator)
    all_ids = set(data.member_ids)
    all_ids.add(actor_id)
    for uid in all_ids:
        m = ConversationMember(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            user_id=uid,
            tenant_id=tenant_id,
        )
        db.add(m)

    await emit_event(db, "GROUP.CREATED", "conversation", conv.id,
                     {"title": data.title, "members": list(all_ids)},
                     actor_id, tenant_id)
    await db.flush()
    return conv


async def add_member(db: AsyncSession, conversation_id: str, user_id: str,
                     tenant_id: str) -> ConversationMember:
    m = ConversationMember(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        user_id=user_id,
        tenant_id=tenant_id,
    )
    db.add(m)
    await db.flush()
    return m


async def get_conversation(db: AsyncSession, conv_id: str, tenant_id: str) -> Conversation | None:
    return (await db.execute(
        select(Conversation).where(Conversation.id == conv_id, Conversation.tenant_id == tenant_id)
    )).scalar_one_or_none()


async def get_group_members(db: AsyncSession, conv_id: str) -> list[ConversationMember]:
    return list((await db.execute(
        select(ConversationMember).where(ConversationMember.conversation_id == conv_id)
    )).scalars().all())


async def list_conversations(db: AsyncSession, tenant_id: str,
                             conv_type: str | None = None,
                             user_id: str | None = None) -> list[Conversation]:
    """List conversations. If user_id given, include cross-tenant conversations
    (groups and direct) where this user is a member."""
    stmt = select(Conversation).where(Conversation.tenant_id == tenant_id)
    if conv_type:
        stmt = stmt.where(Conversation.conv_type == conv_type)
    convs = list((await db.execute(stmt.order_by(Conversation.created_at.desc()))).scalars().all())

    # Also fetch conversations where user is a direct member (cross-tenant)
    if user_id:
        member_sub = (
            select(ConversationMember.conversation_id)
            .where(ConversationMember.user_id == user_id)
        ).subquery()
        member_stmt = (
            select(Conversation)
            .where(Conversation.id.in_(member_sub))
            .where(Conversation.conv_type.in_(["group", "direct"]))
            .order_by(Conversation.created_at.desc())
        )
        member_convs = list((await db.execute(member_stmt)).scalars().all())
        # Deduplicate by id
        seen = {c.id for c in convs}
        for g in member_convs:
            if g.id not in seen:
                convs.append(g)
                seen.add(g.id)

    return convs


async def post_message(db: AsyncSession, data: MessageCreate, tenant_id: str, actor_id: str) -> Message:
    msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=data.conversation_id,
        sender_id=actor_id,
        msg_type=data.msg_type,
        content=data.content,
        parent_msg_id=data.parent_msg_id,
        tenant_id=tenant_id,
    )
    db.add(msg)

    # Update conversation preview
    preview = data.content[:100] + ("..." if len(data.content) > 100 else "")
    from sqlalchemy import update as sql_update
    await db.execute(
        sql_update(Conversation)
        .where(Conversation.id == data.conversation_id)
        .values(last_msg_preview=preview, last_msg_at=func.now())
    )

    await emit_event(db, "MSG.POSTED", "message", msg.id,
                     {"conversation_id": data.conversation_id}, actor_id, tenant_id)
    await db.flush()
    return msg


async def get_messages(db: AsyncSession, conversation_id: str, tenant_id: str,
                       limit: int = 50, offset: int = 0) -> list[Message]:
    return list((await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.tenant_id == tenant_id)
        .order_by(Message.created_at.desc())
        .offset(offset).limit(limit)
    )).scalars().all())


async def add_tag(db: AsyncSession, data: TagCreate, tenant_id: str, actor_id: str) -> MsgTag:
    tag = MsgTag(
        id=str(uuid.uuid4()),
        message_id=data.message_id,
        tag_type=data.tag_type,
        tag_value=data.tag_value,
        tagged_by=data.tagged_by,
        confidence=data.confidence,
        tenant_id=tenant_id,
    )
    db.add(tag)
    await db.flush()
    return tag