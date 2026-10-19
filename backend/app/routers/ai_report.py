"""AI 汇报 API - 交互式任务管理"""
import datetime
from fastapi import APIRouter, Depends, Body
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.notification import Notification, StatusEnum, RelevanceEnum
from app.models.todo import TodoItem, TodoStatus
from app.models.exam import Exam
from app.services.llm_service import llm_service

router = APIRouter()


@router.post("/report")
async def generate_report(db: AsyncSession = Depends(get_db)):
    """生成 AI 汇报（用户主动点击触发）"""
    today = datetime.datetime.utcnow()
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - datetime.timedelta(days=7)

    # 待办：当天及以后的所有待办
    todo_result = await db.execute(
        select(TodoItem).where(
            TodoItem.status == TodoStatus.PENDING,
            or_(TodoItem.deadline >= today_start, TodoItem.deadline == None),
        ).order_by(TodoItem.deadline)
    )
    todos = [
        {
            "id": t.id,
            "content": t.content,
            "deadline": t.deadline.isoformat() if t.deadline else None,
            "location": t.location,
        }
        for t in todo_result.scalars().all()
    ]

    # 已完成待办（本周）
    completed_result = await db.execute(
        select(TodoItem).where(
            TodoItem.status == TodoStatus.COMPLETED,
            TodoItem.created_at >= week_ago,
        ).order_by(TodoItem.deadline)
    )
    completed_todos = [
        {"id": t.id, "content": t.content}
        for t in completed_result.scalars().all()
    ]

    # 考试
    exam_result = await db.execute(
        select(Exam).where(Exam.exam_time >= today).order_by(Exam.exam_time)
    )
    exams = [
        {
            "id": e.id,
            "subject": e.subject,
            "exam_time": e.exam_time.isoformat() if e.exam_time else None,
            "location": e.location,
        }
        for e in exam_result.scalars().all()
    ]

    # 未处理通知
    notif_result = await db.execute(
        select(Notification).where(
            Notification.status == StatusEnum.PENDING,
        )
    )
    pending_notifications = notif_result.scalars().all()

    recent_notifs = await db.execute(
        select(Notification).where(Notification.created_at >= week_ago)
    )
    weekly_count = len(recent_notifs.scalars().all())
    weekly_completed = len(completed_todos)

    # AI 生成汇报文本
    report_text = await llm_service.generate_report(todos, exams, pending_notifications, completed_todos)

    return {
        "report": report_text,
        "stats": {
            "pending_todos": len(todos),
            "upcoming_exams": len(exams),
            "pending_notifications": len(pending_notifications),
            "weekly_processed": weekly_count,
            "weekly_completed": weekly_completed,
        },
        "generated_at": datetime.datetime.utcnow().isoformat(),
    }

@router.post("/report/chat")
async def chat_with_ai(
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """用户与 AI 对话：汇报后续沟通，AI 自动更新任务状态"""
    messages = body.get("messages", [])
    today = datetime.datetime.utcnow()
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)

    # 获取当前待办和考试上下文
    todo_result = await db.execute(
        select(TodoItem).where(
            TodoItem.status == TodoStatus.PENDING,
            or_(TodoItem.deadline >= today_start, TodoItem.deadline == None),
        ).order_by(TodoItem.deadline)
    )
    all_todos = [
        {"id": t.id, "content": t.content, "deadline": t.deadline.isoformat() if t.deadline else None}
        for t in todo_result.scalars().all()
    ]

    exam_result = await db.execute(
        select(Exam).where(Exam.exam_time >= today).order_by(Exam.exam_time)
    )
    all_exams = [
        {"id": e.id, "subject": e.subject, "exam_time": e.exam_time.isoformat() if e.exam_time else None}
        for e in exam_result.scalars().all()
    ]

    # 让 LLM 分析用户意图并决定操作
    result = await llm_service.handle_report_chat(messages, all_todos, all_exams)

    # 执行 AI 建议的操作
    actions = result.get("actions", [])
    feedback_lines = []

    for action in actions:
        action_type = action.get("type", "")
        target_id = action.get("id")

        if action_type == "complete_todo" and target_id:
            todo = (await db.execute(select(TodoItem).where(TodoItem.id == target_id))).scalar_one_or_none()
            if todo and todo.status == TodoStatus.PENDING:
                todo.status = TodoStatus.COMPLETED
                feedback_lines.append(f"✅ 已完成：{todo.content}")

        elif action_type == "cancel_todo" and target_id:
            todo = (await db.execute(select(TodoItem).where(TodoItem.id == target_id))).scalar_one_or_none()
            if todo and todo.status == TodoStatus.PENDING:
                todo.status = TodoStatus.CANCELLED
                feedback_lines.append(f"❌ 已取消：{todo.content}")

        elif action_type == "confirm_notification":
            notif = (await db.execute(select(Notification).where(Notification.id == target_id))).scalar_one_or_none()
            if notif:
                notif.status = StatusEnum.CONFIRMED
                notif.confirmed_at = datetime.datetime.utcnow()
                feedback_lines.append(f"📌 已确认通知：{notif.raw_content[:50]}...")

        elif action_type == "reject_notification":
            notif = (await db.execute(select(Notification).where(Notification.id == target_id))).scalar_one_or_none()
            if notif:
                notif.status = StatusEnum.REJECTED
                feedback_lines.append(f"🗑️ 已忽略通知：{notif.raw_content[:50]}...")

    await db.commit()

    # 构造回复
    reply = result.get("reply", "好的，已为你处理。")
    if feedback_lines:
        reply += "\n\n" + "\n".join(feedback_lines)

    # 更新后的待办统计
    pending_remaining = (await db.execute(
        select(TodoItem).where(TodoItem.status == TodoStatus.PENDING)
    )).scalars().all()

    return {
        "reply": reply,
        "actions_taken": len(feedback_lines),
        "remaining_todos": len(pending_remaining),
    }
