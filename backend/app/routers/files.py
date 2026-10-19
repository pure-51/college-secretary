"""文件下载统一服务（ADR 000 §4：GET /api/files/{path}，白名单校验防穿越）"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings

router = APIRouter(tags=["文件"])

_ALLOWED_DOWNLOAD_EXT = {".docx", ".xlsx", ".pdf", ".png", ".jpg", ".jpeg", ".txt", ".csv"}


@router.get("/api/files/{path:path}")
async def get_file(path: str):
    export_root = settings.EXPORT_DIR.resolve()
    target = (export_root / path).resolve()
    if not str(target).startswith(str(export_root)):
        raise HTTPException(status_code=403, detail="非法路径")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if target.suffix.lower() not in _ALLOWED_DOWNLOAD_EXT:
        raise HTTPException(status_code=403, detail="文件类型不允许")
    return FileResponse(str(target), filename=target.name)
