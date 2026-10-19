"""收件箱 API - 消息导入/AI处理/用户确认/归档"""
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.notification import Notification, RelevanceEnum, StatusEnum
from app.models.todo import TodoItem, TodoStatus
from app.models.exam import Exam
from app.services.llm_service import llm_service
from app.services.ocr_service import ocr_service
from app.services.web_scraper import web_scraper
from app.utils.file_storage import save_uploaded_file
from pydantic import BaseModel

router = APIRouter()

class ImportMessageRequest(BaseModel):
    source_type: str  # text | image | link
    raw_content: str
    source_url: str | None = None

class ConfirmRequest(BaseModel):
    user_notes: str | None = None
    archive: bool = False  # True = 收件箱一键转档案（S4，ADR §7 裁决）

@router.post("/messages")
async def import_message(
    request: ImportMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """导入新消息（文本/链接）并触发AI处理"""
    notification = Notification(
        source_type=request.source_type,
        raw_content=request.raw_content,
        source_url=request.source_url,
        status=StatusEnum.PENDING,
        relevance=RelevanceEnum.PENDING,
        created_at=datetime.datetime.utcnow(),
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    # 如果是链接，先抓取内容
    if request.source_type == "link":
        content = await web_scraper.fetch_text(request.raw_content)
        notification.raw_content = content
    else:
        content = request.raw_content

    # 异步执行 AI 处理
    await _process_notification(notification, db)

    return {
        "id": notification.id,
        "source_type": notification.source_type,
        "raw_content": notification.raw_content[:200],
        "category": notification.category,
        "status": notification.status.value,
    }

@router.post("/messages/image")
async def import_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """导入图片消息并触发AI处理"""
    filepath = await save_uploaded_file(await file.read(), file.filename or "image.png")

    # OCR 识别
    ocr_text = await ocr_service.recognize(filepath)

    notification = Notification(
        source_type="image",
        raw_content=ocr_text,
        image_path=str(filepath),
        status=StatusEnum.PENDING,
        relevance=RelevanceEnum.PENDING,
        created_at=datetime.datetime.utcnow(),
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    await _process_notification(notification, db)

    return {
        "id": notification.id,
        "source_type": "image",
        "raw_content": notification.raw_content[:200],
        "category": notification.category,
        "status": notification.status.value,
    }

async def _process_notification(notification: Notification, db: AsyncSession):
    """AI处理管道：分类→提取待办→提取考试→判断相关性"""
    content = notification.raw_content

    # 1. 分类
    classification = await llm_service.classify_message(content)
    notification.category = classification.get("category", "其他")
    notification.category_confidence = classification.get("confidence", 0.0)

    # 2. 提取待办
    todos = await llm_service.extract_todos(content)
    for todo_data in todos:
        deadline = None
        if todo_data.get("deadline") and todo_data["deadline"] != "null":
            try:
                deadline = datetime.datetime.fromisoformat(todo_data["deadline"].replace("Z", ""))
            except (ValueError, AttributeError):
                pass
        todo = TodoItem(
            notification_id=notification.id,
            content=todo_data.get("content", ""),
            deadline=deadline,
            location=todo_data.get("location"),
            source_original=content[:500],
            created_at=datetime.datetime.utcnow(),
        )
        db.add(todo)

    # 3. 提取考试安排
    exams = await llm_service.extract_exams(content)
    for exam_data in exams:
        exam_time = None
        if exam_data.get("exam_time") and exam_data["exam_time"] != "null":
            try:
                exam_time = datetime.datetime.fromisoformat(exam_data["exam_time"].replace("Z", ""))
            except (ValueError, AttributeError):
                pass
        exam = Exam(
            notification_id=notification.id,
            subject=exam_data.get("subject", ""),
            exam_time=exam_time or datetime.datetime.utcnow(),
            location=exam_data.get("location"),
            seat_number=exam_data.get("seat_number"),
            source_original=content[:500],
            created_at=datetime.datetime.utcnow(),
        )
        db.add(exam)

    # 4. 相关性判断
    relevance = await llm_service.judge_relevance(content)
    notification.relevance = RelevanceEnum.RELEVANT if relevance.get("relevant", True) else RelevanceEnum.IRRELEVANT

    notification.processed_at = datetime.datetime.utcnow()
    await db.commit()

@router.get("/messages")
async def list_messages(
    status: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取消息列表（可分页）"""
    query = select(Notification).order_by(Notification.created_at.desc())
    if status:
        query = query.where(Notification.status == status)
    if category:
        query = query.where(Notification.category == category)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": n.id,
                "source_type": n.source_type,
                "raw_content": n.raw_content,
                "category": n.category,
                "relevance": n.relevance.value if n.relevance else "pending",
                "status": n.status.value if n.status else "pending",
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in items
        ],
        "total": len(items),
    }

@router.get("/messages/{message_id}")
async def get_message(message_id: int, db: AsyncSession = Depends(get_db)):
    """获取消息详情"""
    result = await db.execute(select(Notification).where(Notification.id == message_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(404, "消息不存在")

    # 获取关联的待办和考试
    todos_result = await db.execute(
        select(TodoItem).where(TodoItem.notification_id == message_id)
    )
    exams_result = await db.execute(
        select(Exam).where(Exam.notification_id == message_id)
    )

    return {
        "id": notification.id,
        "source_type": notification.source_type,
        "raw_content": notification.raw_content,
        "category": notification.category,
        "relevance": notification.relevance.value if notification.relevance else "pending",
        "status": notification.status.value if notification.status else "pending",
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
        "todos": [
            {"content": t.content, "deadline": t.deadline.isoformat() if t.deadline else None, "location": t.location}
            for t in todos_result.scalars().all()
        ],
        "exams": [
            {"subject": e.subject, "exam_time": e.exam_time.isoformat() if e.exam_time else None, "location": e.location}
            for e in exams_result.scalars().all()
        ],
    }

@router.put("/messages/{message_id}/confirm")
async def confirm_message(
    message_id: int,
    request: ConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    """用户确认处理结果"""
    result = await db.execute(select(Notification).where(Notification.id == message_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(404, "消息不存在")

    notification.status = StatusEnum.CONFIRMED
    notification.confirmed_at = datetime.datetime.utcnow()
    notification.user_notes = request.user_notes

    # S4 联动：一键转档案（建 pending 档案，来源=本通知）
    archived = False
    if request.archive:
        from app.models.archive_record import ArchiveRecord
        archive = ArchiveRecord(
            record_type="certificate",
            title=notification.raw_content[:50],
            fields={"source": "inbox", "content": notification.raw_content[:500]},
            summary=notification.raw_content[:500],
            sensitivity="internal",
            record_status="pending",
            source_notification_id=notification.id,
        )
        db.add(archive)
        archived = True

    await db.commit()

    return {"status": "confirmed", "archived": archived}

@router.put("/messages/{message_id}/reject")
async def reject_message(
    message_id: int,
    request: ConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    """用户拒绝/需要修改"""
    result = await db.execute(select(Notification).where(Notification.id == message_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(404, "消息不存在")

    notification.status = StatusEnum.REJECTED
    notification.user_notes = request.user_notes
    await db.commit()

    return {"status": "rejected"}

@router.put("/messages/{message_id}/irrelevant")
async def mark_irrelevant(message_id: int, db: AsyncSession = Depends(get_db)):
    """标记为与我无关"""
    result = await db.execute(select(Notification).where(Notification.id == message_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(404, "消息不存在")

    notification.relevance = RelevanceEnum.IRRELEVANT
    await db.commit()

    return {"status": "irrelevant"}

@router.post("/messages/{message_id}/reprocess")
async def reprocess_message(message_id: int, db: AsyncSession = Depends(get_db)):
    """重新AI处理"""
    result = await db.execute(select(Notification).where(Notification.id == message_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(404, "消息不存在")

    # 清除旧的待办和考试
    await db.execute(TodoItem.__table__.delete().where(TodoItem.notification_id == message_id))  # type: ignore
    await db.execute(Exam.__table__.delete().where(Exam.notification_id == message_id))  # type: ignore

    await _process_notification(notification, db)
    return {"status": "reprocessed"}


@router.delete("/messages/{message_id}")
async def delete_message(message_id: int, db: AsyncSession = Depends(get_db)):
    """删除消息及其关联的待办和考试"""
    result = await db.execute(select(Notification).where(Notification.id == message_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(404, "消息不存在")

    # 删除关联的待办和考试
    await db.execute(TodoItem.__table__.delete().where(TodoItem.notification_id == message_id))
    await db.execute(Exam.__table__.delete().where(Exam.notification_id == message_id))

    await db.delete(notification)
    await db.commit()

    return {"status": "deleted"}


@router.delete("/messages")
async def clear_all_messages(db: AsyncSession = Depends(get_db)):
    """清空所有消息、待办和考试"""
    await db.execute(TodoItem.__table__.delete())
    await db.execute(Exam.__table__.delete())
    await db.execute(Notification.__table__.delete())
    await db.commit()
    return {"status": "cleared"}
