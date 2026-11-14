from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response, ErrorCode
from app.schemas.production import IssueCreate, WipReportCreate, FgReceiptCreate
from app.services import production as srv

router = APIRouter(tags=["production"])


@router.post("/issues")
async def create_issue(body: IssueCreate, db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    issue = await srv.create_issue(db, body, user["tenant_id"], user["user_id"])
    await db.commit()
    return success_response(data={"id": issue.id, "qty": issue.qty})


@router.post("/wip-reports")
async def create_wip_report(body: WipReportCreate, db: AsyncSession = Depends(get_db),
                             user: dict = Depends(get_current_user)):
    try:
        r = await srv.create_wip_report(db, body, user["tenant_id"], user["user_id"])
    except ValueError as e:
        raise HTTPException(422, detail={"code": ErrorCode.UNPROCESSABLE, "message": str(e)})
    await db.commit()
    return success_response(data={"id": r.id, "process_code": r.process_code, "qty_out": r.qty_out})


@router.post("/fg-receipts")
async def create_fg_receipt(body: FgReceiptCreate, db: AsyncSession = Depends(get_db),
                             user: dict = Depends(get_current_user)):
    try:
        fg = await srv.create_fg_receipt(db, body, user["tenant_id"], user["user_id"])
    except ValueError as e:
        raise HTTPException(409, detail={"code": ErrorCode.CONFLICT, "message": str(e)})
    await db.commit()
    return success_response(data={"id": fg.id, "sn": fg.sn, "qty": fg.qty})