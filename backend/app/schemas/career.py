"""A 域请求/响应契约（ADR 000 §4 冻结，简历五段/证据链/体检响应唯一来源）"""
from typing import Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """证据链契约：无来源时 source_document_id 为 null → 标【待补充】"""
    source_document_id: Optional[int] = None
    chunk_id: Optional[int] = None
    page: Optional[int] = None
    confidence: float = 0.0


class ArchiveRecordIn(BaseModel):
    record_type: str = "activity"  # honor|score|internship|activity|skill|paper_meta|ledger|signup_row|certificate
    title: str = ""
    fields: dict = Field(default_factory=dict)
    summary: Optional[str] = None
    evidence: Evidence = Field(default_factory=Evidence)
    sensitivity: str = "internal"
    record_status: str = "pending"
    source_notification_id: Optional[int] = None


class ArchiveRecordUpdate(BaseModel):
    title: Optional[str] = None
    fields: Optional[dict] = None
    summary: Optional[str] = None
    evidence: Optional[Evidence] = None
    sensitivity: Optional[str] = None
    record_status: Optional[str] = None


class ResumeGenerateReq(BaseModel):
    direction: str = "保研-计算机"
    archive_record_ids: Optional[list[int]] = None  # None = 全部档案
    template: str = ""


class ResumeLineOut(BaseModel):
    text: str = ""
    evidence: Optional[Evidence] = None
    missing: bool = False  # True = 无来源，前端显示【待补充】


class ResumeSectionOut(BaseModel):
    title: str = ""
    lines: list[ResumeLineOut] = Field(default_factory=list)


class ResumeOut(BaseModel):
    sections: list[ResumeSectionOut] = Field(default_factory=list)
    gaps: list[dict] = Field(default_factory=list)


class InterviewFeedbackReq(BaseModel):
    direction: str = ""
    qa_pairs: list[dict] = Field(default_factory=list)


class FeedbackScore(BaseModel):
    expression: float = 0.0
    professional: float = 0.0
    logic: float = 0.0
    fit: float = 0.0


class FeedbackOut(BaseModel):
    score: FeedbackScore = Field(default_factory=FeedbackScore)
    feedback: str = ""
    advice: str = ""


class HealthDimension(BaseModel):
    field: str = ""
    required: bool = False
    filled: bool = False
    evidence: bool = False


class HealthCheckOut(BaseModel):
    progress: int = 0  # 0-100
    dimensions: list[HealthDimension] = Field(default_factory=list)
    gaps: list[dict] = Field(default_factory=list)
