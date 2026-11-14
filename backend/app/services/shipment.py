import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.shipment import Shipment, ShipmentLine, GoodsReceipt
from app.schemas.shipment import ShipmentCreate, GoodsReceiptCreate
from app.events.bus import emit_event


def _gen_dn_no() -> str:
    from datetime import datetime
    now = datetime.now()
    seq = str(uuid.uuid4().int)[:3]
    return f"DN-{now.strftime('%Y%m%d')}-{seq}"


async def create_shipment(db: AsyncSession, data: ShipmentCreate, tenant_id: str, actor_id: str) -> Shipment:
    s = Shipment(
        id=str(uuid.uuid4()),
        dn_no=_gen_dn_no(),
        wo_id=data.wo_id,
        idh_id=data.idh_id,
        status="draft",
        eta=data.eta,
        carrier=data.carrier,
        tracking_no=data.tracking_no,
        tenant_id=tenant_id,
    )
    db.add(s)
    await db.flush()

    for i, line_data in enumerate(data.lines, 1):
        line = ShipmentLine(
            id=str(uuid.uuid4()),
            shipment_id=s.id,
            line_no=i,
            material_id=line_data.material_id,
            lot_id=line_data.lot_id,
            container_id=line_data.container_id,
            parent_container_id=line_data.parent_container_id,
            container_type=line_data.container_type,
            qty_per_container=line_data.qty_per_container,
            qty_shipped=line_data.qty_shipped,
            tenant_id=tenant_id,
        )
        db.add(line)

    await emit_event(db, "DN.CREATED", "shipment", s.dn_no,
                     {"dn_no": s.dn_no, "wo_id": data.wo_id}, actor_id, tenant_id)
    await db.flush()
    return s


async def confirm_shipment(db: AsyncSession, s: Shipment, actor_id: str, tenant_id: str) -> Shipment:
    s.status = "shipped"
    db.add(s)
    await emit_event(db, "DN.SHIPPED", "shipment", s.dn_no,
                     {"dn_no": s.dn_no, "status": "shipped"}, actor_id, tenant_id)
    await db.flush()
    return s


async def create_goods_receipt(db: AsyncSession, data: GoodsReceiptCreate,
                                tenant_id: str, actor_id: str) -> GoodsReceipt:
    # Check idempotency
    existing = (await db.execute(
        select(GoodsReceipt).where(
            GoodsReceipt.dn_no == data.dn_no,
            GoodsReceipt.container_id == data.container_id,
            GoodsReceipt.tenant_id == tenant_id,
        )
    )).scalar_one_or_none()
    if existing:
        raise ValueError("该容器已收货，不可重复")

    gr = GoodsReceipt(
        id=str(uuid.uuid4()),
        dn_no=data.dn_no,
        container_id=data.container_id,
        lot_id=data.lot_id,
        qty_received=data.qty_received,
        qty_shipped=data.qty_shipped,
        diff_reason=data.diff_reason,
        received_by=data.received_by,
        tenant_id=tenant_id,
    )
    db.add(gr)
    await emit_event(db, "GR.CONFIRMED", "goods_receipt", data.dn_no,
                     {"dn_no": data.dn_no, "container_id": data.container_id,
                      "qty_received": data.qty_received}, actor_id, tenant_id)
    await db.flush()
    return gr


async def list_shipments(db: AsyncSession, tenant_id: str, wo_id: str | None = None,
                         offset: int = 0, limit: int = 20) -> tuple[list[Shipment], int]:
    stmt = select(Shipment).where(Shipment.tenant_id == tenant_id)
    count_q = select(func.count()).select_from(Shipment).where(Shipment.tenant_id == tenant_id)
    if wo_id:
        stmt = stmt.where(Shipment.wo_id == wo_id)
        count_q = count_q.where(Shipment.wo_id == wo_id)
    stmt = stmt.order_by(Shipment.created_at.desc()).offset(offset).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_q)).scalar() or 0
    return list(rows), total


async def get_shipment(db: AsyncSession, s_id: str, tenant_id: str) -> Shipment | None:
    return (await db.execute(
        select(Shipment).where(Shipment.id == s_id, Shipment.tenant_id == tenant_id)
    )).scalar_one_or_none()


async def get_shipment_lines(db: AsyncSession, shipment_id: str) -> list[ShipmentLine]:
    return list((await db.execute(
        select(ShipmentLine).where(ShipmentLine.shipment_id == shipment_id).order_by(ShipmentLine.line_no)
    )).scalars().all())