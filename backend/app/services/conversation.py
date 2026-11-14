import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, ConversationMember, Message, MsgTag
from app.schemas.conversation import ConversationCreate, MessageCreate, TagCreate
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


async def list_conversations(db: AsyncSession, tenant_id: str,
                             conv_type: str | None = None) -> list[Conversation]:
    stmt = select(Conversation).where(Conversation.tenant_id == tenant_id)
    if conv_type:
        stmt = stmt.where(Conversation.conv_type == conv_type)
    return list((await db.execute(stmt.order_by(Conversation.created_at.desc()))).scalars().all())


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