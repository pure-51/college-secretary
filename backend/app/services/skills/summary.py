"""摘要技能（迁移自旧 llm_service，版本 v1，行为保持不变）"""
from app.services.skills.base import build_skill


generate = build_skill(
    "summary.generate",
    output_schema=None,  # 纯文本输出
    temperature=0.3,
    max_tokens=1024,
    cache_ttl=300,
    json_mode=False,
)

SKILLS = [generate]
