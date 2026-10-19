"""日程 API - 待办事项和考试安排"""
import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.todo import TodoItem, TodoStatus
from app.models.exam import Exam

router = APIRouter()

@router.get("/events")
async def list_events(
    date: str = Query(None, description="查询日期 (YYYY-MM-DD)"),
    upcoming: bool = Query(False, description="仅获取即将到来的事项"),
    db: AsyncSession = Depends(get_db),
):
    """获取所有事项（待办+考试）"""
    events = []

    # 待办事项
    todo_query = select(TodoItem).where(TodoItem.status != TodoStatus.CANCELLED)
    if date:
        try:
            target = datetime.datetime.fromisoformat(date)
            next_day = target + datetime.timedelta(days=1)
            todo_query = todo_query.where(
                and_(TodoItem.deadline >= target, TodoItem.deadline < next_day)
            )
        except ValueError:
            pass

    todo_result = await db.execute(todo_query.order_by(TodoItem.deadline))
    for t in todo_result.scalars().all():
        events.append({
            "id": t.id,
            "type": "todo",
            "content": t.content,
            "time": t.deadline.isoformat() if t.deadline else None,
            "location": t.location,
            "status": t.status.value if t.status else "pending",
        })

    # 考试安排
    exam_query = select(Exam)
    if date:
        try:
            target = datetime.datetime.fromisoformat(date)
            next_day = target + datetime.timedelta(days=1)
            exam_query = exam_query.where(
                and_(Exam.exam_time >= target, Exam.exam_time < next_day)
            )
        except ValueError:
            pass

    exam_result = await db.execute(exam_query.order_by(Exam.exam_time))
    for e in exam_result.scalars().all():
        events.append({
            "id": e.id,
            "type": "exam",
            "content": f"{e.subject} 考试",
            "time": e.exam_time.isoformat() if e.exam_time else None,
            "location": e.location,
            "seat": e.seat_number,
        })

    # 按时间排序
    events.sort(key=lambda x: x.get("time") or "")

    return {"items": events, "total": len(events)}

@router.get("/todos")
async def list_todos(
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取待办事项列表"""
    query = select(TodoItem).order_by(TodoItem.deadline)
    if status:
        query = query.where(TodoItem.status == status)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": t.id,
                "content": t.content,
                "deadline": t.deadline.isoformat() if t.deadline else None,
                "location": t.location,
                "status": t.status.value if t.status else "pending",
                "source": t.source_original[:100] if t.source_original else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in items
        ],
        "total": len(items),
    }

@router.put("/todos/{todo_id}")
async def update_todo(
    todo_id: int,
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """更新待办状态"""
    result = await db.execute(select(TodoItem).where(TodoItem.id == todo_id))
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(404, "待办不存在")

    if status:
        try:
            todo.status = TodoStatus(status)
        except ValueError:
            raise HTTPException(400, "无效的状态值")

    await db.commit()
    return {"status": "updated"}

@router.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int, db: AsyncSession = Depends(get_db)):
    """删除待办"""
    result = await db.execute(select(TodoItem).where(TodoItem.id == todo_id))
    todo = result.scalar_one_or_none()
    if not todo:
        raise HTTPException(404, "待办不存在")

    await db.delete(todo)
    await db.commit()
    return {"status": "deleted"}

@router.get("/exams")
async def list_exams(db: AsyncSession = Depends(get_db)):
    """获取考试安排列表"""
    result = await db.execute(select(Exam).order_by(Exam.exam_time))
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": e.id,
                "subject": e.subject,
                "exam_time": e.exam_time.isoformat() if e.exam_time else None,
                "location": e.location,
                "seat_number": e.seat_number,
                "notes": e.notes,
            }
            for e in items
        ],
        "total": len(items),
    }


@router.delete("/exams/{exam_id}")
async def delete_exam(exam_id: int, db: AsyncSession = Depends(get_db)):
    """删除考试安排"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(404, "考试不存在")

    await db.delete(exam)
    await db.commit()
    return {"status": "deleted"}


@router.delete("/all")
async def clear_all_schedule(db: AsyncSession = Depends(get_db)):
    """清空所有待办和考试"""
    await db.execute(TodoItem.__table__.delete())
    await db.execute(Exam.__table__.delete())
    await db.commit()
    return {"status": "cleared"}
