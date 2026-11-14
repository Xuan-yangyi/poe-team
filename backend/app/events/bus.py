import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.events.models import EventLog


async def emit_event(
    db: AsyncSession,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict | None = None,
    actor_id: str = "",
    tenant_id: str = "",
) -> EventLog:
    event = EventLog(
        id=f"evt-{uuid.uuid4().hex[:12]}",
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload or {},
        actor_id=actor_id,
        tenant_id=tenant_id,
    )
    db.add(event)
    await db.flush()
    return event