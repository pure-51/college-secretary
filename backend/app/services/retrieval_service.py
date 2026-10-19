"""检索服务（ADR 000 §4：rerank 精排；§7 裁决：候选 >5 触发 LLM 精排，否则按原序）"""
from app.services.llm_service import llm_service

# 触发阈值（ADR §7）
RERANK_THRESHOLD = 5


async def rerank(query: str, candidates: list[dict]) -> list[dict]:
    """候选精排：>5 条走 LLM；否则保持原序。
    candidates: [{id, title, content}]；返回按相关度排序的候选（含 score/reason）。
    """
    if not candidates:
        return []
    if len(candidates) <= RERANK_THRESHOLD:
        return [
            {**c, "score": 1.0 - i * 0.05, "reason": "候选较少，按原序"}  # 保序，附保守分数
            for i, c in enumerate(candidates)
        ]
    try:
        out = await llm_service.rerank(query, candidates)
        ranked = out.get("ranked", [])
        by_id = {r.get("id"): r for r in ranked}
        # 按 LLM 排序输出，未覆盖的候选排最后
        ordered = [c for r in ranked for c in candidates if c.get("id") == r.get("id")]
        ordered += [c for c in candidates if c.get("id") not in {r.get("id") for r in ranked}]
        return [
            {**c, "score": by_id.get(c.get("id"), {}).get("score", 0.0),
             "reason": by_id.get(c.get("id"), {}).get("reason", "")}
            for c in ordered
        ]
    except Exception:
        # LLM 失败降级：保序
        return [c for c in candidates]
