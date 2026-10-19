"""遗留域技能迁移（ADR 000 §1：consult/report/documents 三域）
chat_query / generate / handle_chat / compare
chat_query 与 generate 为纯文本输出（json_mode=False，调用方期望 str）；
handle_chat 与 compare 为 JSON 输出（调用方期望 dict）。
"""
from typing import Optional
from pydantic import BaseModel, Field

from app.services.skills.base import build_skill


class HandleChatAction(BaseModel):
    type: str = ""
    id: Optional[int] = None


class HandleChatOut(BaseModel):
    reply: str = ""
    actions: list[HandleChatAction] = Field(default_factory=list)


class DiffItem(BaseModel):
    type: str = "modified"  # added|removed|modified
    section: str = ""
    summary: str = ""


class CompareOut(BaseModel):
    diffs: list[DiffItem] = Field(default_factory=list)
    overall_summary: str = ""


chat_query = build_skill(
    "consult.chat_query",
    output_schema=None,  # 纯文本
    temperature=0.3,
    max_tokens=2048,
    cache_ttl=300,
    json_mode=False,
)
generate = build_skill(
    "report.generate",
    output_schema=None,  # 纯文本
    temperature=0.5,
    max_tokens=2048,
    cache_ttl=300,
    json_mode=False,
)
handle_chat = build_skill(
    "report.handle_chat",
    output_schema=HandleChatOut,
    temperature=0.3,
    max_tokens=2048,
    cache_ttl=0,
)
compare = build_skill(
    "documents.compare",
    output_schema=CompareOut,
    temperature=0.1,
    max_tokens=2048,
    cache_ttl=0,
)

SKILLS = [chat_query, generate, handle_chat, compare]
