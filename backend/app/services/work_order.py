import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.work_order import WorkOrder, WoLine
from app.schemas.work_order import WorkOrderCreate, WorkOrderAccept, WorkOrderChange
from app.events.bus import emit_event


def _gen_wo_no() -> str:
    from datetime import datetime
    now = datetime.now()
    seq = str(uuid.uuid4().int)[:3]
    return f"WO-{now.strftime('%Y%m%d')}-{seq}"


async def create_work_order(db: AsyncSession, data: WorkOrderCreate, tenant_id: str, actor_id: str) -> WorkOrder:
    wo = WorkOrder(
        id=str(uuid.uuid4()),
        wo_no=_gen_wo_no(),
        idh_id=data.idh_id,
        customer_id=data.customer_id,
        status="draft",
        due_date=data.due_date,
        bom_ver=data.bom_ver,
        settle_mode=data.settle_mode,
        priority=data.priority,
        tenant_id=tenant_id,
    )
    db.add(wo)
    await db.flush()

    for i, line_data in enumerate(data.lines, 1):
        line = WoLine(
            id=str(uuid.uuid4()),
            wo_id=wo.id,
            line_no=i,
            material_id=line_data.material_id,
            qty_ordered=line_data.qty_ordered,
            unit_price=line_data.unit_price,
            tenant_id=tenant_id,
        )
        db.add(line)

    await emit_event(db, "WO.CREATED", "work_order", wo.wo_no,
                     {"wo_no": wo.wo_no, "status": "draft"}, actor_id, tenant_id)
    await db.flush()
    return wo


async def issue_work_order(db: AsyncSession, wo: WorkOrder, actor_id: str, tenant_id: str) -> WorkOrder:
    wo.status = "issued"
    db.add(wo)
    await emit_event(db, "WO.ISSUED", "work_order", wo.wo_no,
                     {"wo_no": wo.wo_no, "status": "issued"}, actor_id, tenant_id)
    await db.flush()
    return wo


async def accept_work_order(db: AsyncSession, wo: WorkOrder, data: WorkOrderAccept,
                            actor_id: str, tenant_id: str) -> WorkOrder:
    wo.status = "accepted"
    if data.confirmed_due_date:
        wo.confirmed_due_date = data.confirmed_due_date
    db.add(wo)
    await emit_event(db, "WO.ACCEPTED", "work_order", wo.wo_no,
                     {"wo_no": wo.wo_no, "confirmed_due_date": str(data.confirmed_due_date) if data.confirmed_due_date else None},
                     actor_id, tenant_id)
    await db.flush()
    return wo


async def change_work_order(db: AsyncSession, wo: WorkOrder, data: WorkOrderChange,
                            actor_id: str, tenant_id: str) -> WorkOrder:
    wo.status = data.change_type
    db.add(wo)
    await emit_event(db, f"WO.{data.change_type.upper()}", "work_order", wo.wo_no,
                     {"wo_no": wo.wo_no, "reason_code": data.reason_code, "remark": data.remark},
                     actor_id, tenant_id)
    await db.flush()
    return wo


async def list_work_orders(db: AsyncSession, tenant_id: str, status: str | None = None,
                           idh_id: str | None = None, offset: int = 0, limit: int = 20) -> tuple[list[WorkOrder], int]:
    from sqlalchemy import func
    base = select(WorkOrder).where(WorkOrder.tenant_id == tenant_id)
    count_q = select(func.count()).select_from(WorkOrder).where(WorkOrder.tenant_id == tenant_id)

    if status:
        base = base.where(WorkOrder.status == status)
        count_q = count_q.where(WorkOrder.status == status)
    if idh_id:
        base = base.where(WorkOrder.idh_id == idh_id)
        count_q = count_q.where(WorkOrder.idh_id == idh_id)

    base = base.order_by(WorkOrder.created_at.desc()).offset(offset).limit(limit)
    rows = (await db.execute(base)).scalars().all()
    total = (await db.execute(count_q)).scalar() or 0
    return list(rows), total


async def get_work_order(db: AsyncSession, wo_id: str, tenant_id: str) -> WorkOrder | None:
    stmt = select(WorkOrder).where(WorkOrder.id == wo_id, WorkOrder.tenant_id == tenant_id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_wo_lines(db: AsyncSession, wo_id: str) -> list[WoLine]:
    stmt = select(WoLine).where(WoLine.wo_id == wo_id).order_by(WoLine.line_no)
    return list((await db.execute(stmt)).scalars().all())