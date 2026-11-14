import uuid
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reconciliation import ReconPeriod, ReconItem, Adjustment
from app.schemas.reconciliation import ReconPeriodCreate, ReconItemUpdate, AdjustCreate, AdjustApprove
from app.events.bus import emit_event


async def create_period(db: AsyncSession, data: ReconPeriodCreate, tenant_id: str, actor_id: str) -> ReconPeriod:
    period = ReconPeriod(
        period=data.period,
        idh_id=data.idh_id,
        tenant_id=tenant_id,
    )
    db.add(period)
    await emit_event(db, "RECON.PERIOD.CREATED", "recon_period", str(period.id),
                     {"period": data.period, "idh_id": data.idh_id}, actor_id, tenant_id)
    await db.flush()
    return period


async def load_items(db: AsyncSession, period_id: int, items: list[dict], tenant_id: str) -> list[ReconItem]:
    rows = []
    for it in items:
        row = ReconItem(
            period_id=period_id,
            material_id=it["material_id"],
            lot_id=it["lot_id"],
            diff_code=it.get("diff_code", "UNKNOWN"),
            qty_a=it.get("qty_a", 0),
            qty_b=it.get("qty_b", 0),
            qty_c=it.get("qty_c", 0),
            qty_diff=it.get("qty_diff", 0),
            tenant_id=tenant_id,
        )
        db.add(row)
        rows.append(row)
    await db.flush()
    return rows


async def dispute_item(db: AsyncSession, item_id: int, data: ReconItemUpdate,
                       tenant_id: str, actor_id: str) -> ReconItem | None:
    item = (await db.execute(
        select(ReconItem).where(ReconItem.id == item_id, ReconItem.tenant_id == tenant_id)
    )).scalar_one_or_none()
    if not item:
        return None
    item.status = "disputed"
    item.dispute_reason = data.dispute_reason
    item.dispute_attachments = data.dispute_attachments
    item.dispute_at = func.now()
    await emit_event(db, "RECON.ITEM.DISPUTED", "recon_item", str(item.id),
                     {"dispute_reason": data.dispute_reason}, actor_id, tenant_id)
    await db.flush()
    return item


async def get_period(db: AsyncSession, period_id: int, tenant_id: str) -> ReconPeriod | None:
    return (await db.execute(
        select(ReconPeriod).where(ReconPeriod.id == period_id, ReconPeriod.tenant_id == tenant_id)
    )).scalar_one_or_none()


async def get_items(db: AsyncSession, period_id: int, tenant_id: str,
                    diff_code: str | None = None, status: str | None = None) -> list[ReconItem]:
    stmt = select(ReconItem).where(ReconItem.period_id == period_id, ReconItem.tenant_id == tenant_id)
    if diff_code:
        stmt = stmt.where(ReconItem.diff_code == diff_code)
    if status:
        stmt = stmt.where(ReconItem.status == status)
    return list((await db.execute(stmt.order_by(ReconItem.id))).scalars().all())


async def create_adjustment(db: AsyncSession, data: AdjustCreate, tenant_id: str, actor_id: str) -> Adjustment:
    adj_no = f"ADJ-{uuid.uuid4().hex[:8].upper()}"
    adj = Adjustment(
        adj_no=adj_no,
        period_id=data.period_id,
        recon_item_id=data.recon_item_id,
        lot_id=data.lot_id,
        qty_before=data.qty_before,
        qty_after=data.qty_after,
        diff_code=data.diff_code,
        reason=data.reason,
        tenant_id=tenant_id,
    )
    db.add(adj)
    await emit_event(db, "ADJUSTMENT.CREATED", "adjustment", adj_no,
                     {"qty_before": data.qty_before, "qty_after": data.qty_after}, actor_id, tenant_id)
    await db.flush()
    return adj


async def approve_adjustment(db: AsyncSession, adj_id: int, data: AdjustApprove,
                             tenant_id: str, actor_id: str) -> Adjustment | None:
    adj = (await db.execute(
        select(Adjustment).where(Adjustment.id == adj_id, Adjustment.tenant_id == tenant_id)
    )).scalar_one_or_none()
    if not adj:
        return None
    if data.role == "factory":
        adj.factory_approved_by = data.approved_by
        adj.factory_approved_at = func.now()
    elif data.role == "idh":
        adj.idh_approved_by = data.approved_by
        adj.idh_approved_at = func.now()
    if adj.factory_approved_by and adj.idh_approved_by:
        adj.status = "approved"
    await db.flush()
    return adj