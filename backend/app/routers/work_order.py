from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response, ErrorCode
from app.core.pagination import PaginationParams
from app.schemas.work_order import (
    WorkOrderCreate, WorkOrderIssue, WorkOrderAccept, WorkOrderChange,
    WorkOrderListQuery, WorkOrderResponse, WoLineResponse,
)
from app.services import work_order as wo_service

router = APIRouter(prefix="/work-orders", tags=["work-orders"])


@router.post("")
async def create_work_order(
    body: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    wo = await wo_service.create_work_order(db, body, user["tenant_id"], user["user_id"])
    await db.commit()
    return success_response(data={
        "id": wo.id,
        "wo_no": wo.wo_no,
        "status": wo.status,
        "created_at": str(wo.created_at) if wo.created_at else "",
    }, message="工单创建成功")


@router.post("/{wo_id}/issue")
async def issue_work_order(
    wo_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    wo = await wo_service.get_work_order(db, wo_id, user["tenant_id"])
    if not wo:
        raise HTTPException(status_code=404, detail={"code": ErrorCode.NOT_FOUND, "message": "工单不存在"})
    if wo.status != "draft":
        raise HTTPException(status_code=422, detail={"code": ErrorCode.UNPROCESSABLE, "message": f"工单状态 {wo.status} 不可下达"})
    wo = await wo_service.issue_work_order(db, wo, user["user_id"], user["tenant_id"])
    await db.commit()
    return success_response(data={"wo_no": wo.wo_no, "status": wo.status})


@router.post("/{wo_id}/accept")
async def accept_work_order(
    wo_id: str,
    body: WorkOrderAccept,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    wo = await wo_service.get_work_order(db, wo_id, user["tenant_id"])
    if not wo:
        raise HTTPException(status_code=404, detail={"code": ErrorCode.NOT_FOUND, "message": "工单不存在"})
    wo = await wo_service.accept_work_order(db, wo, body, user["user_id"], user["tenant_id"])
    await db.commit()
    return success_response(data={"wo_no": wo.wo_no, "status": wo.status})


@router.post("/{wo_id}/change")
async def change_work_order(
    wo_id: str,
    body: WorkOrderChange,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    wo = await wo_service.get_work_order(db, wo_id, user["tenant_id"])
    if not wo:
        raise HTTPException(status_code=404, detail={"code": ErrorCode.NOT_FOUND, "message": "工单不存在"})
    wo = await wo_service.change_work_order(db, wo, body, user["user_id"], user["tenant_id"])
    await db.commit()
    return success_response(data={"wo_no": wo.wo_no, "status": wo.status})


@router.get("")
async def list_work_orders(
    status: str | None = Query(None),
    idh_id: str | None = Query(None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    params = PaginationParams(page=page, page_size=page_size)
    rows, total = await wo_service.list_work_orders(
        db, user["tenant_id"], status, idh_id, params.offset, params.page_size
    )
    items = []
    for wo in rows:
        lines = await wo_service.get_wo_lines(db, wo.id)
        items.append({
            "id": wo.id, "wo_no": wo.wo_no, "idh_id": wo.idh_id,
            "status": wo.status, "due_date": str(wo.due_date) if wo.due_date else None,
            "settle_mode": wo.settle_mode, "priority": wo.priority,
            "lines": [
                {"id": l.id, "line_no": l.line_no, "material_id": l.material_id,
                 "qty_ordered": l.qty_ordered, "qty_shipped": l.qty_shipped,
                 "qty_received": l.qty_received, "qty_consumed": l.qty_consumed,
                 "unit_price": str(l.unit_price) if l.unit_price else None}
                for l in lines
            ],
            "created_at": str(wo.created_at) if wo.created_at else "",
            "updated_at": str(wo.updated_at) if wo.updated_at else "",
        })
    return success_response(data=items, meta={"page": page, "page_size": page_size, "total": total})


@router.get("/{wo_id}")
async def get_work_order(
    wo_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    wo = await wo_service.get_work_order(db, wo_id, user["tenant_id"])
    if not wo:
        raise HTTPException(status_code=404, detail={"code": ErrorCode.NOT_FOUND, "message": "工单不存在"})
    lines = await wo_service.get_wo_lines(db, wo.id)
    return success_response(data={
        "id": wo.id, "wo_no": wo.wo_no, "idh_id": wo.idh_id,
        "status": wo.status, "due_date": str(wo.due_date) if wo.due_date else None,
        "confirmed_due_date": str(wo.confirmed_due_date) if wo.confirmed_due_date else None,
        "settle_mode": wo.settle_mode, "priority": wo.priority,
        "lines": [
            {"id": l.id, "line_no": l.line_no, "material_id": l.material_id,
             "qty_ordered": l.qty_ordered, "qty_shipped": l.qty_shipped,
             "qty_received": l.qty_received, "qty_consumed": l.qty_consumed}
            for l in lines
        ],
        "created_at": str(wo.created_at) if wo.created_at else "",
        "updated_at": str(wo.updated_at) if wo.updated_at else "",
    })