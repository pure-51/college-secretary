"""长任务中心服务（ADR 000 §3.5 + §4：/api/tasks 创建/轮询/取消/重做）
裁决#10：同步阻塞执行（不互斥锁），但统一返回 task_id 供前端轮询展示进度。
任务回调注册：各域长任务通过 register_handler(skill_name, fn) 接入统一中心。
"""
import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_progress import TaskProgress
from app.database import async_session_factory

# skill_name → 异步执行函数（fn(db, payload) -> dict）
_HANDLERS: dict[str, callable] = {}


def register_handler(skill_name: str, fn: callable) -> None:
    _HANDLERS[skill_name] = fn


def has_handler(skill_name: str) -> bool:
    return skill_name in _HANDLERS


async def create_task(skill_name: str, payload: dict) -> int:
    """创建长任务记录并同步执行；返回 task_id"""
    async with async_session_factory() as db:
        task = TaskProgress(skill_name=skill_name, status="running", progress=0,
                            steps=[{"step": "任务创建", "status": "done", "detail": "已提交"}])
        db.add(task)
        await db.commit()
        await db.refresh(task)
        task_id = task.id

        handler = _HANDLERS.get(skill_name)
        if handler is None:
            task.status = "failed"
            task.error = f"未注册任务处理器: {skill_name}"
            await db.commit()
            return task_id

        try:
            result = await handler(db, payload)
            task.status = "success"
            task.progress = 100
            task.result = result
            for s in task.steps or []:
                s["status"] = "done"
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
        task.updated_at = datetime.datetime.utcnow()
        await db.commit()
        return task_id


async def get_task(db: AsyncSession, task_id: int) -> TaskProgress:
    task = (await db.execute(select(TaskProgress).where(TaskProgress.id == task_id))).scalar_one_or_none()
    if not task:
        raise ValueError(f"任务不存在: {task_id}")
    return task


async def cancel_task(db: AsyncSession, task_id: int) -> TaskProgress:
    """取消：仅标记 cancelled（同步执行无法中途停止，语义为拒绝轮询/前端弃用）"""
    task = await get_task(db, task_id)
    if task.status == "running":
        task.status = "cancelled"
        task.updated_at = datetime.datetime.utcnow()
        await db.commit()
    return task


async def redo_task(db: AsyncSession, task_id: int) -> int:
    """重做：取原任务 skill+result 的 payload 重新执行，返回新 task_id"""
    task = await get_task(db, task_id)
    new_id = await create_task(task.skill_name, task.result or {})
    return new_id
