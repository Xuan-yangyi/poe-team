from enum import IntEnum
from typing import Any, Optional
from fastapi.responses import JSONResponse


class ErrorCode(IntEnum):
    SUCCESS = 0
    VALIDATION_ERROR = 1001
    NOT_FOUND = 1002
    CONFLICT = 1003
    UNPROCESSABLE = 1004
    UNAUTHORIZED = 2001
    FORBIDDEN_CROSS_TENANT = 2002
    FORBIDDEN_ROLE = 2003
    SERVER_ERROR = 3001
    SERVICE_UNAVAILABLE = 3002


HTTP_STATUS_MAP = {
    ErrorCode.SUCCESS: 200,
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.UNPROCESSABLE: 422,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.FORBIDDEN_CROSS_TENANT: 403,
    ErrorCode.FORBIDDEN_ROLE: 403,
    ErrorCode.SERVER_ERROR: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
}


def success_response(
    data: Any = None,
    message: str = "success",
    meta: Optional[dict] = None,
) -> JSONResponse:
    body = {"code": ErrorCode.SUCCESS, "message": message, "data": data}
    if meta:
        body["meta"] = meta
    return JSONResponse(content=body, status_code=200)


def error_response(
    code: ErrorCode,
    message: str = "",
    detail: Any = None,
) -> JSONResponse:
    status = HTTP_STATUS_MAP.get(code, 500)
    body = {"code": code, "message": message, "data": detail}
    return JSONResponse(content=body, status_code=status)
