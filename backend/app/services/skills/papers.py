"""科研论文库技能（B 域，ADR 000 §1）
meta_extract / explain / qa / compare / review_section
"""
from typing import Optional
from pydantic import BaseModel, Field

from app.services.skills.base import build_skill


class PaperMetaOut(BaseModel):
    title: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    language: str = "en"


class ExplainPart(BaseModel):
    title: str = ""
    content: str = ""
    source_chunk_id: Optional[int] = None


class ExplainOut(BaseModel):
    parts: list[ExplainPart] = Field(default_factory=list)


class Citation(BaseModel):
    chunk_id: Optional[int] = None
    document_id: Optional[int] = None
    confidence: float = 0.0


class QAOut(BaseModel):
    answer: str = ""
    citations: list[Citation] = Field(default_factory=list)


class CompareOut(BaseModel):
    table: dict = Field(default_factory=dict)  # {"columns": [...], "rows": [[...]]}


class ReviewCitation(BaseModel):
    document_id: Optional[int] = None
    quote: str = ""


class ReviewSectionOut(BaseModel):
    content: str = ""
    citations: list[ReviewCitation] = Field(default_factory=list)


meta_extract = build_skill("papers.meta_extract", output_schema=PaperMetaOut, temperature=0.1, max_tokens=2048)
explain = build_skill("papers.explain", output_schema=ExplainOut, cache_ttl=0, temperature=0.3, max_tokens=4096)
qa = build_skill("papers.qa", output_schema=QAOut, cache_ttl=0, temperature=0.2, max_tokens=2048)
compare = build_skill("papers.compare", output_schema=CompareOut, cache_ttl=0, temperature=0.2, max_tokens=4096)
review_section = build_skill("papers.review_section", output_schema=ReviewSectionOut, cache_ttl=0, temperature=0.3, max_tokens=4096)

SKILLS = [meta_extract, explain, qa, compare, review_section]
