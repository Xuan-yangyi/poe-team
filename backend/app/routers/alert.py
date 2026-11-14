from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.deps import get_current_user
from app.core.response import success_response, ErrorCode
from app.schemas.alert import AlertAck, AlertResolve
from app.services import alert as srv

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(status: str | None = Query(None), alert_type: str | None = Query(None),
                      severity: str | None = Query(None),
                      page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                      db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    offset = (page - 1) * page_size
    rows, total = await srv.list_alerts(db, user["tenant_id"], status, alert_type, severity, offset, page_size)
    items = [{
        "id": a.id, "alert_type": a.alert_type, "severity": a.severity,
        "title": a.title, "detail": a.detail, "ref_type": a.ref_type, "ref_id": a.ref_id,
        "status": a.status, "acknowledged_by": a.acknowledged_by,
        "resolved_by": a.resolved_by, "resolution": a.resolution
    } for a in rows]
    return success_response(data=items, meta={"page": page, "page_size": page_size, "total": total})


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, body: AlertAck,
                            db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    alert = await srv.acknowledge_alert(db, alert_id, body, user["tenant_id"])
    if not alert:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Alert not found"})
    await db.commit()
    return success_response(data={"id": alert.id, "status": alert.status})


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, body: AlertResolve,
                        db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    alert = await srv.resolve_alert(db, alert_id, body, user["tenant_id"])
    if not alert:
        raise HTTPException(404, detail={"code": ErrorCode.NOT_FOUND, "message": "Alert not found"})
    await db.commit()
    return success_response(data={"id": alert.id, "status": alert.status})