from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response
from app.core.pagination import PaginationParams
from app.services import inventory as srv

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/stock")
async def get_stock(material_id: str | None = Query(None), lot_id: str | None = Query(None),
                    idh_id: str | None = Query(None), status: str | None = Query(None),
                    owner: str | None = Query(None), page: int = Query(1, ge=1),
                    page_size: int = Query(20, ge=1, le=100),
                    db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    p = PaginationParams(page, page_size)
    rows, total = await srv.query_stock(db, user["tenant_id"], material_id, lot_id, idh_id, status, owner,
                                         p.offset, p.page_size)
    items = [{"id": r.id, "material_id": r.material_id, "lot_id": r.lot_id, "idh_id": r.idh_id,
              "owner": r.owner, "status": r.status, "qty_change": r.qty_change, "qty_after": r.qty_after,
              "event_type": r.event_type} for r in rows]
    return success_response(data=items, meta={"page": page, "page_size": page_size, "total": total})


@router.get("/stock-ledger")
async def get_stock_ledger(lot_id: str = Query(...), db: AsyncSession = Depends(get_db),
                           user: dict = Depends(get_current_user)):
    rows = await srv.get_stock_ledger(db, lot_id, user["tenant_id"])
    items = [{"id": r.id, "material_id": r.material_id, "lot_id": r.lot_id,
              "qty_change": r.qty_change, "qty_after": r.qty_after,
              "event_type": r.event_type, "event_id": r.event_id,
              "created_at": str(r.created_at) if r.created_at else ""} for r in rows]
    return success_response(data=items)