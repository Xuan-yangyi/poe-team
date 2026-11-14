from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.stock import StockLedger


async def query_stock(db: AsyncSession, tenant_id: str, material_id: str | None = None,
                      lot_id: str | None = None, idh_id: str | None = None,
                      status: str | None = None, owner: str | None = None,
                      offset: int = 0, limit: int = 20) -> tuple[list[StockLedger], int]:
    stmt = select(StockLedger).where(StockLedger.tenant_id == tenant_id)
    count_q = select(func.count()).select_from(StockLedger).where(StockLedger.tenant_id == tenant_id)

    if material_id:
        stmt = stmt.where(StockLedger.material_id == material_id)
        count_q = count_q.where(StockLedger.material_id == material_id)
    if lot_id:
        stmt = stmt.where(StockLedger.lot_id == lot_id)
        count_q = count_q.where(StockLedger.lot_id == lot_id)
    if idh_id:
        stmt = stmt.where(StockLedger.idh_id == idh_id)
        count_q = count_q.where(StockLedger.idh_id == idh_id)
    if status:
        stmt = stmt.where(StockLedger.status == status)
        count_q = count_q.where(StockLedger.status == status)
    if owner:
        stmt = stmt.where(StockLedger.owner == owner)
        count_q = count_q.where(StockLedger.owner == owner)

    stmt = stmt.order_by(StockLedger.created_at.desc()).offset(offset).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_q)).scalar() or 0
    return list(rows), total


async def get_stock_ledger(db: AsyncSession, lot_id: str, tenant_id: str, limit: int = 100) -> list[StockLedger]:
    return list((await db.execute(
        select(StockLedger).where(StockLedger.lot_id == lot_id, StockLedger.tenant_id == tenant_id)
        .order_by(StockLedger.created_at.desc()).limit(limit)
    )).scalars().all())