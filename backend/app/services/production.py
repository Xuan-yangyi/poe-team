import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.production import Issue, WipReport, FgReceipt
from app.schemas.production import IssueCreate, WipReportCreate, FgReceiptCreate
from app.events.bus import emit_event


async def create_issue(db: AsyncSession, data: IssueCreate, tenant_id: str, actor_id: str) -> Issue:
    issue = Issue(
        id=str(uuid.uuid4()),
        wo_id=data.wo_id,
        lot_id=data.lot_id,
        material_id=data.material_id,
        qty=data.qty,
        operator=data.operator,
        scan_method=data.scan_method,
        tenant_id=tenant_id,
    )
    db.add(issue)
    await emit_event(db, "ISSUE.POSTED", "issue", issue.id,
                     {"wo_id": data.wo_id, "lot_id": data.lot_id, "qty": data.qty},
                     actor_id, tenant_id)
    await db.flush()
    return issue


async def create_wip_report(db: AsyncSession, data: WipReportCreate, tenant_id: str, actor_id: str) -> WipReport:
    if data.qty_out + data.qty_scrap > data.qty_in:
        raise ValueError("产出+报废不能超过投入")
    report = WipReport(
        id=str(uuid.uuid4()),
        wo_id=data.wo_id,
        process_code=data.process_code,
        process_seq=data.process_seq,
        qty_in=data.qty_in,
        qty_out=data.qty_out,
        qty_scrap=data.qty_scrap,
        scrap_reason=data.scrap_reason,
        reported_by=data.reported_by,
        tenant_id=tenant_id,
    )
    db.add(report)
    await emit_event(db, "WIP.REPORTED", "wip_report", report.id,
                     {"wo_id": data.wo_id, "process_code": data.process_code,
                      "qty_out": data.qty_out, "qty_scrap": data.qty_scrap},
                     actor_id, tenant_id)
    await db.flush()
    return report


async def create_fg_receipt(db: AsyncSession, data: FgReceiptCreate, tenant_id: str, actor_id: str) -> FgReceipt:
    existing = (await db.execute(
        select(FgReceipt).where(FgReceipt.sn == data.sn)
    )).scalar_one_or_none()
    if existing:
        raise ValueError(f"SN {data.sn} 已存在")
    fg = FgReceipt(
        id=str(uuid.uuid4()),
        wo_id=data.wo_id,
        sn=data.sn,
        qty=data.qty,
        lot_id=data.lot_id,
        received_by=data.received_by,
        tenant_id=tenant_id,
    )
    db.add(fg)
    await emit_event(db, "FG.RECEIVED", "fg_receipt", fg.sn,
                     {"wo_id": data.wo_id, "sn": data.sn, "qty": data.qty},
                     actor_id, tenant_id)
    await db.flush()
    return fg