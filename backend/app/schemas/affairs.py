"""D 域班务请求/响应契约（ADR 000 §4 冻结）"""
from typing import Optional
from pydantic import BaseModel, Field


class NoticeGenerateReq(BaseModel):
    """D1 通知生成"""
    scene: str = ""
    key_points: list[str] = Field(default_factory=list)
    tone: str = ""


class SignupCreateReq(BaseModel):
    """D2 创建接龙"""
    title: str
    description: Optional[str] = None
    options: list[str] = Field(default_factory=list)
    deadline: Optional[str] = None  # ISO 字符串，后端解析


class SignupImportReq(BaseModel):
    """D2 批量导入+去重"""
    raw_text: str = ""
    source: str = "text"  # text|image|manual


class LedgerImportReq(BaseModel):
    """D3 台账导入（P1）"""
    ocr_text: str = ""
