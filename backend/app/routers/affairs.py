"""班务助理 API（D 域，ADR 000 §4：9 端点）
D1 通知生成 / D2 接龙（创建/导入去重/统计/导出/未报名催办）/ D3 台账（导入/导出）
接龙去重：UNIQUE(signup_id, name) 覆盖式更新（ADR §7 裁决）；台账金额只存本地、展示打码（ADR §6）。
"""
import datetime
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.signup import Signup, SignupEntry
from app.models.ledger import LedgerEntry
from app.models.todo import TodoItem
from app.models.todo_link import TodoLink
from app.schemas.affairs import NoticeGenerateReq, SignupCreateReq, SignupImportReq, LedgerImportReq
from app.services.llm_service import llm_service
from app.services import export_service

router = APIRouter(prefix="/api/affairs", tags=["班务助理"])


def _mask_amount(amount: float) -> str:
    """金额打码展示（ADR §6：只显示 ¥***）"""
    if amount is None:
        return "¥***"
    sign = "-" if amount < 0 else ""
    return f"{sign}¥***"


async def _get_signup(db: AsyncSession, signup_id: int) -> Signup:
    s = (await db.execute(select(Signup).where(Signup.id == signup_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "接龙不存在")
    return s


# ================= D1 通知生成 =================

@router.post("/notices/generate")
async def generate_notice(req: NoticeGenerateReq, db: AsyncSession = Depends(get_db)):
    """D1 通知生成（草稿+精简复制版）"""
    if not req.scene:
        raise HTTPException(400, "请提供通知场景")
    try:
        out = await llm_service.notice_generate(req.scene, req.key_points, req.tone)
    except Exception as e:
        raise HTTPException(502, f"通知生成失败: {e}")
    return {"draft": out.get("draft", ""), "copy_text": out.get("copy_text", "")}


# ================= D2 接龙 =================

@router.post("/signups")
async def create_signup(req: SignupCreateReq, db: AsyncSession = Depends(get_db)):
    """D2 创建接龙"""
    if not req.title.strip():
        raise HTTPException(400, "请提供接龙标题")
    deadline = None
    if req.deadline:
        try:
            deadline = datetime.datetime.fromisoformat(req.deadline)
        except ValueError:
            raise HTTPException(400, "deadline 需为 ISO 时间字符串")
    s = Signup(
        title=req.title.strip(),
        description=req.description,
        options=req.options,
        deadline=deadline,
        status="open",
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return {"id": s.id, "title": s.title, "status": s.status}


@router.post("/signups/{signup_id}/import")
async def import_signup(signup_id: int, req: SignupImportReq, db: AsyncSession = Depends(get_db)):
    """D2 批量导入名单 + 去重（同名覆盖式更新）"""
    signup = await _get_signup(db, signup_id)
    if not req.raw_text.strip():
        raise HTTPException(400, "请提供接龙文本")
    try:
        parsed = await llm_service.signup_parse(req.raw_text)
    except Exception as e:
        raise HTTPException(502, f"接龙解析失败: {e}")

    entries = parsed.get("entries", [])
    added = 0
    updated = 0
    for e in entries:
        name = (e.get("name") or "").strip()
        if not name:
            continue
        existing = (await db.execute(
            select(SignupEntry).where(SignupEntry.signup_id == signup_id, SignupEntry.name == name)
        )).scalar_one_or_none()
        if existing:
            # 覆盖式更新（ADR §7：UNIQUE(signup_id, name)）
            existing.detail = e.get("detail") or existing.detail
            existing.option = e.get("option") or existing.option
            existing.source = req.source
            updated += 1
        else:
            db.add(SignupEntry(
                signup_id=signup_id,
                name=name,
                detail=e.get("detail"),
                option=e.get("option"),
                source=req.source,
                is_duplicate=False,
            ))
            added += 1
    await db.commit()

    stats = await _signup_stats(db, signup_id)
    return {"added": added, "updated": updated, "stats": stats}


@router.get("/signups/{signup_id}")
async def get_signup_stats(signup_id: int, db: AsyncSession = Depends(get_db)):
    """接龙统计（契约冻结：{signup, entries, stats:{total, unique, per_option, unsubmitted}}）"""
    signup = await _get_signup(db, signup_id)
    entries = (await db.execute(
        select(SignupEntry).where(SignupEntry.signup_id == signup_id).order_by(SignupEntry.created_at)
    )).scalars().all()
    return {
        "signup": {"id": signup.id, "title": signup.title, "options": signup.options or [], "status": signup.status},
        "entries": [
            {"id": e.id, "name": e.name, "detail": e.detail, "option": e.option,
             "source": e.source, "is_duplicate": e.is_duplicate}
            for e in entries
        ],
        "stats": await _signup_stats(db, signup_id, entries),
    }


async def _signup_stats(db: AsyncSession, signup_id: int, entries: list = None) -> dict:
    """接龙统计（唯一去重按 name）"""
    if entries is None:
        entries = (await db.execute(
            select(SignupEntry).where(SignupEntry.signup_id == signup_id)
        )).scalars().all()
    unique_names = {e.name for e in entries}
    per_option: dict[str, int] = {}
    for e in entries:
        opt = e.option or "未表态"
        per_option[opt] = per_option.get(opt, 0) + 1
    return {
        "total": len(entries),
        "unique": len(unique_names),
        "per_option": per_option,
        "unsubmitted": 0,  # 未报名人数由前端基于总名单推导
    }


@router.post("/signups/{signup_id}/export")
async def export_signup(signup_id: int, db: AsyncSession = Depends(get_db)):
    """接龙导出 xlsx"""
    signup = await _get_signup(db, signup_id)
    entries = (await db.execute(
        select(SignupEntry).where(SignupEntry.signup_id == signup_id).order_by(SignupEntry.created_at)
    )).scalars().all()
    rows = [[e.name, e.detail or "", e.option or "", e.source] for e in entries]
    try:
        filename = export_service.export_xlsx(["姓名", "备注", "选项", "来源"], rows)
    except Exception as e:
        raise HTTPException(400, f"导出失败: {e}")
    return {"file_url": f"/api/files/{filename}", "filename": filename}


@router.post("/signups/{signup_id}/todo")
async def signup_unsubmitted_todo(signup_id: int, db: AsyncSession = Depends(get_db)):
    """未报名名单 → 待办进日程（来源=signup 角标）"""
    signup = await _get_signup(db, signup_id)
    entries = (await db.execute(
        select(SignupEntry).where(SignupEntry.signup_id == signup_id)
    )).scalars().all()
    submitted = {e.name for e in entries}
    todo = TodoItem(content=f"催办接龙「{signup.title}」未报名名单（共 {max(len(submitted), 0)} 人已报）",
                    deadline=signup.deadline, status="pending")
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    link = TodoLink(todo_id=todo.id, source_type="signup", source_id=signup_id, label="接龙")
    db.add(link)
    await db.commit()
    return {"todo_id": todo.id, "submitted_count": len(submitted)}


# ================= D3 台账 =================

@router.post("/ledger/import")
async def import_ledger(req: LedgerImportReq, db: AsyncSession = Depends(get_db)):
    """D3 台账导入（P1）：OCR 文本 → 条目，金额打码落库"""
    if not req.ocr_text.strip():
        raise HTTPException(400, "请提供台账文本")
    try:
        parsed = await llm_service.ledger_extract(req.ocr_text)
    except Exception as e:
        raise HTTPException(502, f"台账解析失败: {e}")

    added = 0
    for e in parsed.get("entries", []):
        item = (e.get("item") or "").strip()
        if not item:
            continue
        amount = e.get("amount")
        date = None
        if e.get("date"):
            try:
                date = datetime.date.fromisoformat(e["date"])
            except ValueError:
                date = None
        db.add(LedgerEntry(
            date=date,
            item=item,
            amount=amount,  # 原始金额仅本地存储（ADR §6）
            amount_masked=_mask_amount(amount),
            category=e.get("category"),
            status="pending",
        ))
        added += 1
    await db.commit()
    return {"added": added}


@router.post("/ledger/export")
async def export_ledger(db: AsyncSession = Depends(get_db)):
    """台账导出（P1）：金额列输出打码值"""
    entries = (await db.execute(select(LedgerEntry).order_by(LedgerEntry.created_at.desc()))).scalars().all()
    rows = [
        [e.date.isoformat() if e.date else "", e.item or "", e.amount_masked or "¥***", e.category or ""]
        for e in entries
    ]
    try:
        filename = export_service.export_xlsx(["日期", "项目", "金额", "类别"], rows)
    except Exception as e:
        raise HTTPException(400, f"导出失败: {e}")
    return {"file_url": f"/api/files/{filename}", "filename": filename, "total": len(entries)}
