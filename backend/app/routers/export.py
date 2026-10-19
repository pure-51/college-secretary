"""统一导出 API（ADR 000 §4：POST /api/export/docx | /api/export/xlsx）"""
from fastapi import APIRouter, HTTPException

from app.services import export_service

router = APIRouter(prefix="/api/export", tags=["导出"])


@router.post("/docx")
async def export_docx(payload: dict):
    title = str(payload.get("title", "导出文档"))[:200]
    blocks = payload.get("blocks") or []
    try:
        filename = export_service.export_docx(title, blocks)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导出失败: {e}")
    return {"file_url": f"/api/files/{filename}"}


@router.post("/xlsx")
async def export_xlsx(payload: dict):
    headers = payload.get("headers") or []
    rows = payload.get("rows") or []
    try:
        filename = export_service.export_xlsx(headers, rows)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导出失败: {e}")
    return {"file_url": f"/api/files/{filename}"}
