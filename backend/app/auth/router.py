from fastapi import APIRouter, HTTPException
from app.auth.schemas import LoginRequest, TokenResponse, RefreshRequest
from app.auth.service import authenticate, create_tokens, AuthError
from app.core.response import success_response, ErrorCode
from app.core.security import decode_token, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest):
    try:
        user = authenticate(body.username, body.password)
    except AuthError as e:
        raise HTTPException(status_code=401, detail={"code": e.code, "message": e.message})
    tokens = create_tokens(user)
    return success_response(data=tokens)


@router.post("/refresh")
async def refresh(body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail={
            "code": ErrorCode.UNAUTHORIZED, "message": "Invalid refresh token"
        })
    # In production, also check refresh token blacklist / rotation
    user_id = payload["sub"]
    claims = {k: v for k, v in payload.items() if k not in ("sub", "exp", "type", "iat")}
    access_token = create_access_token(user_id, extra_claims=claims)
    refresh_token = create_refresh_token(user_id)
    return success_response(data={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 15 * 60,
    })