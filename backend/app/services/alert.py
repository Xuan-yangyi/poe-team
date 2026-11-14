from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.alert import Alert
from app.schemas.alert import AlertAck, AlertResolve


async def list_alerts(db: AsyncSession, tenant_id: str, status: str | None = None,
                      alert_type: str | None = None, severity: str | None = None,
                      offset: int = 0, limit: int = 20) -> tuple[list[Alert], int]:
    stmt = select(Alert).where(Alert.tenant_id == tenant_id)
    count_q = select(func.count()).select_from(Alert).where(Alert.tenant_id == tenant_id)

    if status:
        stmt = stmt.where(Alert.status == status)
        count_q = count_q.where(Alert.status == status)
    if alert_type:
        stmt = stmt.where(Alert.alert_type == alert_type)
        count_q = count_q.where(Alert.alert_type == alert_type)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
        count_q = count_q.where(Alert.severity == severity)

    stmt = stmt.order_by(Alert.created_at.desc()).offset(offset).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_q)).scalar() or 0
    return list(rows), total


async def acknowledge_alert(db: AsyncSession, alert_id: str, data: AlertAck,
                            tenant_id: str) -> Alert | None:
    alert = (await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.tenant_id == tenant_id)
    )).scalar_one_or_none()
    if not alert:
        return None
    alert.status = "acknowledged"
    alert.acknowledged_by = data.acknowledged_by
    alert.acknowledged_at = func.now()
    await db.flush()
    return alert


async def resolve_alert(db: AsyncSession, alert_id: str, data: AlertResolve,
                        tenant_id: str) -> Alert | None:
    alert = (await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.tenant_id == tenant_id)
    )).scalar_one_or_none()
    if not alert:
        return None
    alert.status = "resolved"
    alert.resolved_by = data.resolved_by
    alert.resolved_at = func.now()
    alert.resolution = data.resolution
    await db.flush()
    return alert