import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.core.deps import get_current_user
from app.core.response import success_response

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
ALLOWED_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "webp", "svg",
    "pdf", "doc", "docx", "xls", "xlsx", "txt", "csv", "zip",
}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    # Validate extension
    if file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    else:
        ext = ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, detail={"code": "BAD_REQUEST", "message": f"不支持的文件类型: .{ext}"})

    # Read content and validate size
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(400, detail={"code": "BAD_REQUEST", "message": "文件大小不能超过 10MB"})

    # Save to disk
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    url = f"/uploads/{filename}"
    return success_response(data={
        "url": url,
        "filename": file.filename,
        "size": len(content),
        "content_type": file.content_type,
    })