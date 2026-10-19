"""本地文件存储管理"""
import uuid
from pathlib import Path
from app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".gif", ".bmp"}

async def save_uploaded_file(file_data: bytes, original_filename: str) -> Path:
    """保存上传文件到本地存储，返回文件路径"""
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".bin"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = settings.UPLOAD_DIR / filename
    with open(filepath, "wb") as f:
        f.write(file_data)
    return filepath

async def delete_file(filepath: Path) -> None:
    """删除文件"""
    if filepath.exists():
        filepath.unlink()
