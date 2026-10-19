"""统一长任务 API（ADR 000 §4：/api/tasks 创建/轮询/取消/重做，P1 含 cancel/redo）"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["长任务"])


class TaskCreateReq(BaseModel):
    skill: str
    payload: dict = Field(default_factory=dict)


@router.post("")
async def create_task(req: TaskCreateReq):
    """创建长任务 {skill, payload} → task_id（同步执行，返回即终态）"""
    if not task_service.has_handler(req.skill):
        raise HTTPException(400, f"未注册的任务技能: {req.skill}")
    try:
        task_id = await task_service.create_task(req.skill, req.payload)
    except Exception as e:
        raise HTTPException(500, f"任务创建失败: {e}")
    return {"task_id": task_id}


@router.get("/{task_id}")
async def get_task_progress(task_id: int, db: AsyncSession = Depends(get_db)):
    """轮询任务进度"""
    try:
        task = await task_service.get_task(db, task_id)
    except ValueError:
        raise HTTPException(404, "任务不存在")
    return {
        "task_id": task.id,
        "skill_name": task.skill_name,
        "status": task.status,
        "progress": task.progress,
        "steps": task.steps or [],
        "result": task.result,
        "error": task.error,
    }


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """取消任务（P1）"""
    try:
        task = await task_service.cancel_task(db, task_id)
    except ValueError:
        raise HTTPException(404, "任务不存在")
    return {"task_id": task.id, "status": task.status}


@router.post("/{task_id}/redo")
async def redo_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """重做任务（P1）"""
    try:
        new_id = await task_service.redo_task(db, task_id)
    except ValueError:
        raise HTTPException(404, "任务不存在")
    return {"task_id": new_id}
