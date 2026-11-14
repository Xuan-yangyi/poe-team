from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response, ErrorCode
from app.core.pagination import PaginationParams
from app.schemas.shipment import ShipmentCreate, GoodsReceiptCreate
from app.services import shipment as srv

router = APIRouter(tags=["shipments"])


@router.post("/shipments")
async def create_shipment(body: ShipmentCreate, db: AsyncSession = Depends(get_db),
                          user: dict = Depends(get_current_user)):
    s = await srv.create_shipment(db, body, user["tenant_id"], user["user_id"])
    await db.commit()
    return success_response(data={"id": s.id, "dn_no": s.dn_no, "status": s.status})


@router.post("/shipments/{s_id}/confirm")
async def confirm_shipment(s_id: str, db: AsyncSession = Depends(get_db),
                           user: dict = Depends(get_current_user)):
    s = await srv.get_shipment(db, s_id, user["tenant_id"])
    if not s:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "发货单不存在"})
    s = await srv.confirm_shipment(db, s, user["user_id"], user["tenant_id"])
    await db.commit()
    return success_response(data={"dn_no": s.dn_no, "status": s.status})


@router.get("/shipments")
async def list_shipments(wo_id: str | None = Query(None), page: int = Query(1, ge=1),
                         page_size: int = Query(20, ge=1, le=100),
                         db: AsyncSession = Depends(get_db),
                         user: dict = Depends(get_current_user)):
    p = PaginationParams(page, page_size)
    rows, total = await srv.list_shipments(db, user["tenant_id"], wo_id, p.offset, p.page_size)
    items = [{"id": r.id, "dn_no": r.dn_no, "wo_id": r.wo_id, "status": r.status,
              "eta": str(r.eta) if r.eta else None, "carrier": r.carrier} for r in rows]
    return success_response(data=items, meta={"page": page, "page_size": page_size, "total": total})


@router.get("/shipments/{s_id}")
async def get_shipment(s_id: str, db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    s = await srv.get_shipment(db, s_id, user["tenant_id"])
    if not s:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "发货单不存在"})
    lines = await srv.get_shipment_lines(db, s.id)
    return success_response(data={
        "id": s.id, "dn_no": s.dn_no, "wo_id": s.wo_id, "status": s.status,
        "eta": str(s.eta) if s.eta else None, "carrier": s.carrier, "tracking_no": s.tracking_no,
        "lines": [{"line_no": l.line_no, "container_id": l.container_id,
                    "container_type": l.container_type, "qty_shipped": l.qty_shipped} for l in lines],
    })


@router.post("/goods-receipts")
async def create_goods_receipt(body: GoodsReceiptCreate, db: AsyncSession = Depends(get_db),
                                user: dict = Depends(get_current_user)):
    try:
        gr = await srv.create_goods_receipt(db, body, user["tenant_id"], user["user_id"])
    except ValueError as e:
        raise HTTPException(409, detail={"code": ErrorCode.CONFLICT, "message": str(e)})
    await db.commit()
    return success_response(data={"id": gr.id, "dn_no": gr.dn_no, "qty_received": gr.qty_received})