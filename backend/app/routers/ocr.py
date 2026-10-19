"""OCR 识别 API"""
from fastapi import APIRouter, UploadFile, File
from app.services.ocr_service import ocr_service
from app.utils.file_storage import save_uploaded_file

router = APIRouter()

@router.post("/ocr")
async def recognize_image(file: UploadFile = File(...)):
    """识别图片中的文字"""
    filepath = await save_uploaded_file(await file.read(), file.filename or "image.png")
    text = await ocr_service.recognize(filepath)
    return {"text": text}
