"""班务助理技能（D 域，ADR 000 §1）
notice / signup_parse / ledger_extract
"""
from typing import Optional
from pydantic import BaseModel, Field

from app.services.skills.base import build_skill


class NoticeOut(BaseModel):
    draft: str = ""
    copy_text: str = ""


class SignupEntryOut(BaseModel):
    name: str = ""
    detail: Optional[str] = None
    option: Optional[str] = None


class SignupParseOut(BaseModel):
    entries: list[SignupEntryOut] = Field(default_factory=list)


class LedgerEntryOut(BaseModel):
    date: Optional[str] = None
    item: str = ""
    amount: Optional[float] = None
    category: Optional[str] = None


class LedgerExtractOut(BaseModel):
    entries: list[LedgerEntryOut] = Field(default_factory=list)


notice = build_skill("affairs.notice", output_schema=NoticeOut, cache_ttl=0, temperature=0.3, max_tokens=2048)
signup_parse = build_skill("affairs.signup_parse", output_schema=SignupParseOut, cache_ttl=0, temperature=0.1)
ledger_extract = build_skill("affairs.ledger_extract", output_schema=LedgerExtractOut, cache_ttl=0, temperature=0.1)

SKILLS = [notice, signup_parse, ledger_extract]
