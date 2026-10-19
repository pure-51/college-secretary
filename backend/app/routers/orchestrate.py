"""统一意图路由 API（ADR 000 §4：POST /api/ai/orchestrate）
返回契约冻结：{domain, task, params, reply, needs_clarification, evidence}
domain 枚举完整：career|papers|affairs|schedule|inbox|assistant
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/ai", tags=["AI 路由"])


class OrchestrateReq(BaseModel):
    query: str
    context: str = ""


@router.post("/orchestrate")
async def orchestrate(req: OrchestrateReq, db: AsyncSession = Depends(get_db)):
    """统一意图路由：判断域 → 返回技能/参数/澄清"""
    if not req.query.strip():
        raise HTTPException(400, "请输入请求内容")
    try:
        out = await llm_service.route_intent(req.query, req.context)
    except Exception as e:
        raise HTTPException(502, f"意图路由失败: {e}")
    return {
        "domain": out.get("domain", "assistant"),
        "task": out.get("task", ""),
        "params": out.get("params", {}),
        "reply": out.get("reply", ""),
        "needs_clarification": out.get("needs_clarification", False),
        "evidence": out.get("evidence", []),
    }
