"""统一调度技能（ADR 000 §1）
orchestrate.route（意图路由）/ retrieval.rerank（检索精排）
"""
from typing import Optional
from pydantic import BaseModel, Field

from app.services.skills.base import build_skill


class OrchestrateEvidence(BaseModel):
    """路由引用的证据（ADR §2）"""
    source_document_id: Optional[int] = None
    chunk_id: Optional[int] = None
    confidence: float = 0.0


class OrchestrateOut(BaseModel):
    domain: str = "assistant"  # career|papers|affairs|schedule|inbox|assistant
    task: str = ""
    params: dict = Field(default_factory=dict)
    reply: str = ""
    needs_clarification: bool = False
    evidence: list[OrchestrateEvidence] = Field(default_factory=list)


class RankedItem(BaseModel):
    id: int = 0
    score: float = 0.0
    reason: str = ""


class RerankOut(BaseModel):
    ranked: list[RankedItem] = Field(default_factory=list)


route = build_skill("orchestrate.route", output_schema=OrchestrateOut, cache_ttl=0, temperature=0.1)
rerank = build_skill("retrieval.rerank", output_schema=RerankOut, cache_ttl=0, temperature=0.1)

SKILLS = [route, rerank]
