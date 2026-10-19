"""pydantic 请求/响应契约（ADR 000 §4：唯一来源）"""
from app.schemas.career import (
    Evidence,
    ArchiveRecordIn,
    ArchiveRecordUpdate,
    ResumeGenerateReq,
    ResumeOut,
    ResumeSectionOut,
    ResumeLineOut,
    InterviewFeedbackReq,
    FeedbackScore,
    FeedbackOut,
    HealthCheckOut,
)
from app.schemas.papers import (
    PaperMetaUpdate,
    PaperExplainReq,
    PaperQAReq,
    PaperCompareReq,
    PaperReviewReq,
)
from app.schemas.affairs import (
    NoticeGenerateReq,
    SignupCreateReq,
    SignupImportReq,
    LedgerImportReq,
)

__all__ = [
    "Evidence",
    "ArchiveRecordIn",
    "ArchiveRecordUpdate",
    "ResumeGenerateReq",
    "ResumeOut",
    "ResumeSectionOut",
    "ResumeLineOut",
    "InterviewFeedbackReq",
    "FeedbackScore",
    "FeedbackOut",
    "HealthCheckOut",
    "PaperMetaUpdate",
    "PaperExplainReq",
    "PaperQAReq",
    "PaperCompareReq",
    "PaperReviewReq",
    "NoticeGenerateReq",
    "SignupCreateReq",
    "SignupImportReq",
    "LedgerImportReq",
]
