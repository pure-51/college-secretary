"""OCR 识别服务"""
from pathlib import Path
import numpy as np
import cv2
from app.config import settings


class OCRService:
    def __init__(self):
        self._reader = None

    def _get_reader(self):
        """延迟初始化 EasyOCR"""
        if self._reader is None and settings.OCR_ENABLED:
            try:
                import easyocr
                self._reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
            except ImportError:
                print("⚠️ EasyOCR 未安装，OCR 功能不可用")
                return None
        return self._reader

    async def recognize(self, image_path: str | Path) -> str:
        """识别图片中的文字（支持中文路径）"""
        reader = self._get_reader()
        if reader is None:
            return "[OCR 未配置]"

        try:
            # 用二进制方式读取文件，避免中文路径问题
            with open(image_path, "rb") as f:
                file_bytes = np.frombuffer(f.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if img is None:
                return "[OCR 识别失败: 无法解码图片]"

            result = reader.readtext(img)
            lines = [item[1] for item in result]
            return "\n".join(lines)
        except Exception as e:
            return f"[OCR 识别失败: {e}]"


ocr_service = OCRService()
