from math import ceil
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


class PaginationParams:
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), 100)
        self.offset = (self.page - 1) * self.page_size


async def paginate(
    session: AsyncSession,
    stmt,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list, dict]:
    params = PaginationParams(page, page_size)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0
    rows = (await session.execute(
        stmt.offset(params.offset).limit(params.page_size)
    )).scalars().all()
    meta = {
        "page": params.page,
        "page_size": params.page_size,
        "total": total,
        "total_pages": ceil(total / params.page_size) if total else 0,
    }
    return list(rows), meta
