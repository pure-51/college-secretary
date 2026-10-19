"""生涯档案官技能（A 域 Hero，ADR 000 §1）
archive_extract / resume_generate / interview_questions / interview_feedback / personal_statement
"""
from typing import Optional
from pydantic import BaseModel, Field

from app.services.skills.base import build_skill


class ArchiveExtractOut(BaseModel):
    record_type: str = "activity"  # honor|score|internship|activity|skill|paper_meta|ledger|signup_row|certificate
    title: str = ""
    fields: dict = Field(default_factory=dict)
    evidence_confidence: float = 0.0


class ResumeLine(BaseModel):
    text: str = ""
    source_key: Optional[str] = None  # 证据链回跳键；None = 无来源，标【待补充】
    missing: bool = False


class ResumeSection(BaseModel):
    title: str = ""
    lines: list[ResumeLine] = Field(default_factory=list)


class ResumeGap(BaseModel):
    field: str = ""
    suggestion: str = ""


class ResumeGenerateOut(BaseModel):
    sections: list[ResumeSection] = Field(default_factory=list)
    gaps: list[ResumeGap] = Field(default_factory=list)


class InterviewQuestion(BaseModel):
    question: str = ""
    focus: str = ""  # 考察点
    related_record_id: Optional[int] = None


class InterviewQuestionsOut(BaseModel):
    questions: list[InterviewQuestion] = Field(default_factory=list)


class InterviewScore(BaseModel):
    expression: float = 0.0
    professional: float = 0.0
    logic: float = 0.0
    fit: float = 0.0


class InterviewFeedbackOut(BaseModel):
    score: InterviewScore = Field(default_factory=InterviewScore)
    feedback: str = ""
    advice: str = ""


class PersonalStatementOut(BaseModel):
    statement: str = ""
    strengths: list[str] = Field(default_factory=list)
    plans: list[str] = Field(default_factory=list)


archive_extract = build_skill("career.archive_extract", output_schema=ArchiveExtractOut, cache_ttl=0, temperature=0.1)
resume_generate = build_skill("career.resume_generate", output_schema=ResumeGenerateOut, cache_ttl=0, temperature=0.3, max_tokens=4096)
interview_questions = build_skill("career.interview_questions", output_schema=InterviewQuestionsOut, cache_ttl=0, temperature=0.3)
interview_feedback = build_skill("career.interview_feedback", output_schema=InterviewFeedbackOut, cache_ttl=0, temperature=0.2)
personal_statement = build_skill("career.personal_statement", output_schema=PersonalStatementOut, cache_ttl=0, temperature=0.3, max_tokens=4096)

SKILLS = [archive_extract, resume_generate, interview_questions, interview_feedback, personal_statement]
