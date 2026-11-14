from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response, ErrorCode
from app.schemas.reconciliation import ReconPeriodCreate, ReconItemUpdate, AdjustCreate, AdjustApprove
from app.services import reconciliation as srv

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


@router.post("/periods")
async def create_period(body: ReconPeriodCreate, db: AsyncSession = Depends(get_db),
                        user: dict = Depends(get_current_user)):
    period = await srv.create_period(db, body, user["tenant_id"], user["user_id"])
    await db.commit()
    return success_response(data={"id": period.id, "period": period.period, "idh_id": period.idh_id})


@router.get("/periods/{period_id}")
async def get_period(period_id: int, db: AsyncSession = Depends(get_db),
                     user: dict = Depends(get_current_user)):
    period = await srv.get_period(db, period_id, user["tenant_id"])
    if not period:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Period not found"})
    return success_response(data={
        "id": period.id, "period": period.period, "idh_id": period.idh_id,
        "status": period.status, "total_items": period.total_items,
        "matched": period.matched, "diff_count": period.diff_count
    })


@router.get("/periods/{period_id}/items")
async def get_items(period_id: int, diff_code: str | None = Query(None),
                    status: str | None = Query(None),
                    db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    items = await srv.get_items(db, period_id, user["tenant_id"], diff_code, status)
    return success_response(data=[{
        "id": it.id, "material_id": it.material_id, "lot_id": it.lot_id,
        "diff_code": it.diff_code, "qty_a": it.qty_a, "qty_b": it.qty_b,
        "qty_c": it.qty_c, "qty_diff": it.qty_diff, "status": it.status,
        "dispute_reason": it.dispute_reason
    } for it in items])


@router.put("/items/{item_id}/dispute")
async def dispute_item(item_id: int, body: ReconItemUpdate,
                       db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    item = await srv.dispute_item(db, item_id, body, user["tenant_id"], user["user_id"])
    if not item:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Item not found"})
    await db.commit()
    return success_response(data={"id": item.id, "status": item.status})


@router.post("/adjustments")
async def create_adjustment(body: AdjustCreate, db: AsyncSession = Depends(get_db),
                            user: dict = Depends(get_current_user)):
    adj = await srv.create_adjustment(db, body, user["tenant_id"], user["user_id"])
    await db.commit()
    return success_response(data={"id": adj.id, "adj_no": adj.adj_no, "status": adj.status})


@router.post("/adjustments/{adj_id}/approve")
async def approve_adjustment(adj_id: int, body: AdjustApprove,
                             db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    adj = await srv.approve_adjustment(db, adj_id, body, user["tenant_id"], user["user_id"])
    if not adj:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Adjustment not found"})
    await db.commit()
    return success_response(data={"id": adj.id, "adj_no": adj.adj_no, "status": adj.status})