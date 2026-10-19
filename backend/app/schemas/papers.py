"""B 域论文库请求/响应契约（ADR 000 §4 冻结）"""
from typing import Optional
from pydantic import BaseModel, Field


class PaperMetaUpdate(BaseModel):
    """题录人工补录（PUT /api/papers/meta/{document_id}）"""
    title: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    language: Optional[str] = None


class PaperExplainReq(BaseModel):
    """通俗讲解请求（长任务）"""
    question: str = ""
    document_id: Optional[int] = None


class PaperQAReq(BaseModel):
    """单篇 Q&A 请求"""
    question: str
    history: list[dict] = Field(default_factory=list)


class PaperCompareReq(BaseModel):
    """多篇对比请求（P1）"""
    document_ids: list[int] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)


class PaperReviewReq(BaseModel):
    """综述生成请求（P1 长任务）"""
    document_ids: list[int] = Field(default_factory=list)
    sections: list[str] = Field(default_factory=list)
