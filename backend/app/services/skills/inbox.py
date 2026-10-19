"""收件箱技能（迁移自旧 llm_service，版本 v1，行为保持不变）"""
from typing import Optional
from pydantic import BaseModel, Field

from app.services.skills.base import build_skill


class ClassifyOut(BaseModel):
    category: str = "其他"
    confidence: float = 0.0
    reason: str = "解析失败"


class TodoOut(BaseModel):
    content: str = ""
    deadline: Optional[str] = None
    location: Optional[str] = None


class ExtractTodosOut(BaseModel):
    todos: list[TodoOut] = Field(default_factory=list)


class ExamOut(BaseModel):
    subject: str = ""
    exam_time: Optional[str] = None
    location: Optional[str] = None
    seat_number: Optional[str] = None


class ExtractExamsOut(BaseModel):
    exams: list[ExamOut] = Field(default_factory=list)


class JudgeRelevanceOut(BaseModel):
    relevant: bool = True
    reason: str = "解析失败"


classify = build_skill("inbox.classify", output_schema=ClassifyOut, cache_ttl=300)
extract_todos = build_skill("inbox.extract_todos", output_schema=ExtractTodosOut, cache_ttl=300)
extract_exams = build_skill("inbox.extract_exams", output_schema=ExtractExamsOut, cache_ttl=300)
judge_relevance = build_skill("inbox.judge_relevance", output_schema=JudgeRelevanceOut, cache_ttl=300)

SKILLS = [classify, extract_todos, extract_exams, judge_relevance]
