from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response, ErrorCode
from app.schemas.conversation import ConversationCreate, MessageCreate, TagCreate
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
    convs = await srv.list_conversations(db, user["tenant_id"], conv_type)
    return success_response(data=[{
        "id": c.id, "conv_type": c.conv_type, "ref_id": c.ref_id,
        "title": c.title, "is_active": c.is_active
    } for c in convs])


@router.get("/{conv_id}")
async def get_conversation(conv_id: str, db: AsyncSession = Depends(get_db),
                           user: dict = Depends(get_current_user)):
    conv = await srv.get_conversation(db, conv_id, user["tenant_id"])
    if not conv:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Conversation not found"})
    return success_response(data={
        "id": conv.id, "conv_type": conv.conv_type, "ref_id": conv.ref_id,
        "title": conv.title, "is_active": conv.is_active
    })


@router.post("/{conv_id}/messages")
async def post_message(conv_id: str, body: MessageCreate, db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    body.conversation_id = conv_id
    msg = await srv.post_message(db, body, user["tenant_id"], user["user_id"])
    await db.commit()
    return success_response(data={"id": msg.id, "msg_type": msg.msg_type, "sender_id": msg.sender_id})


@router.get("/{conv_id}/messages")
async def get_messages(conv_id: str, limit: int = Query(50, ge=1, le=200),
                       offset: int = Query(0, ge=0),
                       db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    msgs = await srv.get_messages(db, conv_id, user["tenant_id"], limit, offset)
    return success_response(data=[{
        "id": m.id, "sender_id": m.sender_id, "msg_type": m.msg_type,
        "content": m.content, "parent_msg_id": m.parent_msg_id, "created_at": m.created_at
    } for m in msgs])


@router.post("/tags")
async def add_tag(body: TagCreate, db: AsyncSession = Depends(get_db),
                  user: dict = Depends(get_current_user)):
    tag = await srv.add_tag(db, body, user["tenant_id"], user["user_id"])
    await db.commit()
    return success_response(data={"id": tag.id, "tag_type": tag.tag_type, "tag_value": tag.tag_value})