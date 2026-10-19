"""操作审计（ADR 000 §3.10，P1 骨架：只记元数据不存正文）"""
from typing import Optional

from app.models.audit_log import AuditLog


async def log(
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    metadata: Optional[dict] = None,
    db=None,
) -> None:
    """写 audit_logs。db 未注入时跳过（骨架；S1 挂 run() 后置钩子与写接口装饰器）。"""
    if db is None:
        return
    db.add(AuditLog(action=action, target_type=target_type, target_id=target_id, metadata_=metadata))
    await db.commit()
