"""生涯档案官 API（A 域 Hero，ADR 000 §4：13 端点）
A1 材料归档 → 档案 CRUD+证据链 → 完整性体检 → A2 简历生成 → A3 面试模拟 → 导出。
长任务策略：同步阻塞执行（裁决#10），同时写 task_progress 供前端轮询展示进度。
"""
import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.archive_record import ArchiveRecord
from app.models.artifact import Artifact
from app.models.task_progress import TaskProgress
from app.models.todo_link import TodoLink
from app.models.todo import TodoItem
from app.schemas.career import (
    ArchiveRecordIn,
    ArchiveRecordUpdate,
    ResumeGenerateReq,
    InterviewFeedbackReq,
    FeedbackOut,
    HealthCheckOut,
    Evidence,
)
from app.services.llm_service import llm_service
from app.services import export_service, task_service

router = APIRouter(prefix="/api/career", tags=["生涯档案官"])

# 简历五段完整性体检维度（ADR 未决裁决：无第六段）
_HEALTH_DIMENSIONS = [
    {"field": "个人信息", "record_type": None, "required": True, "suggestion": "补传个人基本信息"},
    {"field": "教育背景", "record_type": None, "required": True, "suggestion": "补传学历/专业信息"},
    {"field": "科研经历", "record_type": "paper_meta", "required": True, "suggestion": "补传论文/科研项目材料"},
    {"field": "荣誉奖项", "record_type": "honor", "required": True, "suggestion": "补传获奖证书"},
    {"field": "技能与课外活动", "record_type": "activity", "required": False, "suggestion": "补传技能/活动经历"},
]


def _rec_to_dict(r: ArchiveRecord) -> dict:
    return {
        "id": r.id,
        "record_type": r.record_type,
        "title": r.title,
        "fields": r.fields or {},
        "summary": r.summary,
        "evidence": Evidence(
            source_document_id=r.evidence_document_id,
            chunk_id=r.evidence_chunk_id,
            page=r.evidence_page,
            confidence=r.evidence_confidence or 0.0,
        ),
        "sensitivity": r.sensitivity,
        "record_status": r.record_status,
    }


def _rec_to_profile_key(r: ArchiveRecord) -> str:
    return f"rec{r.id}"


# ================= A1 材料归档 =================

@router.post("/archive-records")
async def create_archive_record(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """A1 材料归档：OCR/文本 → 结构化抽取 → pending 待确认
    body: {raw_text} 或 {raw_text, record_type_hint}；也可直接 {record: ArchiveRecordIn} 手动录入
    """
    raw_text = (payload.get("raw_text") or "").strip()
    if not raw_text:
        if payload.get("record"):
            rec_in = ArchiveRecordIn(**payload["record"])
            rec = ArchiveRecord(
                record_type=rec_in.record_type,
                title=rec_in.title or "手动录入",
                fields=rec_in.fields,
                summary=rec_in.summary,
                evidence_document_id=rec_in.evidence.source_document_id,
                evidence_chunk_id=rec_in.evidence.chunk_id,
                evidence_page=rec_in.evidence.page,
                evidence_confidence=rec_in.evidence.confidence,
                sensitivity=rec_in.sensitivity,
                record_status=rec_in.record_status,
                source_notification_id=rec_in.source_notification_id,
            )
            db.add(rec)
            await db.commit()
            await db.refresh(rec)
            return {"id": rec.id, "record_type": rec.record_type, "title": rec.title,
                    "fields": rec.fields, "evidence_confidence": rec.evidence_confidence,
                    "record_status": rec.record_status}
        raise HTTPException(400, "请提供 raw_text 或 record 字段")

    category_hint = payload.get("record_type_hint") or ""
    try:
        extracted = await llm_service.archive_extract(raw_text, category_hint)
    except Exception:
        raise HTTPException(502, "归档抽取失败")

    rec = ArchiveRecord(
        record_type=extracted.get("record_type", "activity"),
        title=extracted.get("title", "") or raw_text[:50],
        fields=extracted.get("fields") or {},
        evidence_confidence=extracted.get("evidence_confidence", 0.0),
        record_status="pending",
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return {"id": rec.id, "record_type": rec.record_type, "title": rec.title,
            "fields": rec.fields, "evidence_confidence": rec.evidence_confidence,
            "record_status": rec.record_status}


@router.get("/archive-records")
async def list_archive_records(
    record_type: str | None = None,
    status: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """档案列表（record_type/status/search 过滤）"""
    query = select(ArchiveRecord).order_by(ArchiveRecord.updated_at.desc(), ArchiveRecord.created_at.desc())
    if record_type:
        query = query.where(ArchiveRecord.record_type == record_type)
    if status:
        query = query.where(ArchiveRecord.record_status == status)
    if search:
        query = query.where(or_(
            ArchiveRecord.title.ilike(f"%{search}%"),
            ArchiveRecord.summary.ilike(f"%{search}%"),
        ))
    result = await db.execute(query)
    items = result.scalars().all()
    return {
        "items": [
            {"id": r.id, "record_type": r.record_type, "title": r.title, "fields": r.fields,
             "sensitivity": r.sensitivity, "record_status": r.record_status,
             "evidence_confidence": r.evidence_confidence}
            for r in items
        ],
        "total": len(items),
    }


@router.get("/archive-records/{record_id}")
async def get_archive_record(record_id: int, db: AsyncSession = Depends(get_db)):
    """档案详情 + 证据链"""
    r = (await db.execute(select(ArchiveRecord).where(ArchiveRecord.id == record_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "档案不存在")
    return _rec_to_dict(r)


@router.put("/archive-records/{record_id}")
async def update_archive_record(
    record_id: int,
    payload: ArchiveRecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    """修正字段 / 确认落库（确认门）"""
    r = (await db.execute(select(ArchiveRecord).where(ArchiveRecord.id == record_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "档案不存在")
    data = payload.model_dump(exclude_none=True)
    if "evidence" in data:
        ev = data.pop("evidence") or {}
        r.evidence_document_id = ev.get("source_document_id")
        r.evidence_chunk_id = ev.get("chunk_id")
        r.evidence_page = ev.get("page")
        r.evidence_confidence = ev.get("confidence")
    for key, value in data.items():
        setattr(r, key, value)
    r.updated_at = datetime.datetime.utcnow()
    await db.commit()
    return {"status": "updated", "id": r.id}


@router.delete("/archive-records/{record_id}")
async def delete_archive_record(record_id: int, db: AsyncSession = Depends(get_db)):
    r = (await db.execute(select(ArchiveRecord).where(ArchiveRecord.id == record_id))).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "档案不存在")
    await db.delete(r)
    await db.commit()
    return {"status": "deleted"}


# ================= 完整性体检（纯规则，不走 LLM） =================

@router.get("/health-check", response_model=HealthCheckOut)
async def health_check(db: AsyncSession = Depends(get_db)):
    """档案完整性体检：五段维度 → 缺口清单 → 一键补传"""
    records = (await db.execute(select(ArchiveRecord))).scalars().all()
    by_type: dict[str, list] = {}
    has_personal = any(r.title and ("信息" in (r.title or "") or "林小夏" in (r.title or "")) for r in records)
    has_edu = any(r.record_type == "score" or (r.title and "教育" in (r.title or "")) for r in records)

    dimensions = []
    gaps = []
    for d in _HEALTH_DIMENSIONS:
        field = d["field"]
        if field == "个人信息":
            filled = has_personal
        elif field == "教育背景":
            filled = has_edu
        else:
            pool = [r for r in records if r.record_type == d["record_type"]]
            filled = len(pool) > 0
            by_type[field] = pool
        evidence_ok = False
        if field in ("科研经历", "荣誉奖项"):
            pool = by_type.get(field, [])
            evidence_ok = any(r.evidence_document_id is not None for r in pool)
        dimensions.append({"field": field, "required": d["required"], "filled": filled, "evidence": evidence_ok})
        if d["required"] and not filled:
            gaps.append({"field": field, "suggestion": d["suggestion"], "action": "upload"})

    required_dim = [x for x in dimensions if x["required"]]
    filled_count = sum(1 for x in required_dim if x["filled"])
    progress = round(filled_count / len(required_dim) * 100) if required_dim else 0

    return HealthCheckOut(progress=progress, dimensions=dimensions, gaps=gaps)


# ================= A2 简历生成（长任务） =================

async def _collect_profile(db: AsyncSession, ids: list[int] | None) -> tuple[list[dict], dict[str, dict]]:
    """拉取档案构造 profile_sections（key=rec<id>）与 evidence 映射"""
    query = select(ArchiveRecord).order_by(ArchiveRecord.created_at)
    if ids:
        query = query.where(ArchiveRecord.id.in_(ids))
    records = (await db.execute(query)).scalars().all()
    sections = [
        {
            "id": r.id,
            "key": _rec_to_profile_key(r),
            "record_type": r.record_type,
            "title": r.title,
            "fields": r.fields or {},
            "summary": r.summary,
            "evidence_confidence": r.evidence_confidence,
        }
        for r in records
    ]
    evidence_map = {
        _rec_to_profile_key(r): {
            "source_document_id": r.evidence_document_id,
            "chunk_id": r.evidence_chunk_id,
            "page": r.evidence_page,
            "confidence": r.evidence_confidence or 0.0,
        }
        for r in records
    }
    return sections, evidence_map


async def _run_resume_generate(db: AsyncSession, req: ResumeGenerateReq) -> dict:
    """简历生成核心：构造档案 → LLM → 存 artifact + task_progress"""
    profile_sections, evidence_map = await _collect_profile(db, req.archive_record_ids)
    # 拼接 profile 文本供技能消费
    profile_text = json.dumps(profile_sections, ensure_ascii=False)

    task = TaskProgress(skill_name="career.resume_generate", status="running", progress=10,
                        steps=[{"step": "整理档案", "status": "done", "detail": f"已加载 {len(profile_sections)} 条"}])
    db.add(task)
    await db.commit()
    await db.refresh(task)

    task.steps = [{"step": "整理档案", "status": "done", "detail": f"已加载 {len(profile_sections)} 条"},
                  {"step": "AI 生成", "status": "running", "detail": "根据档案撰写简历"}]
    task.progress = 50
    await db.commit()

    try:
        out = await llm_service.resume_generate(req.direction, profile_sections, req.template)
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        await db.commit()
        raise HTTPException(502, f"简历生成失败: {e}")

    # 证据链映射：source_key=rec<id> 补 evidence；无来源 → missing
    sections = []
    for sec in out.get("sections", []):
        lines = []
        for line in sec.get("lines", []):
            sk = line.get("source_key")
            if sk and sk in evidence_map:
                lines.append({"text": line.get("text", ""), "evidence": evidence_map[sk], "missing": False})
            else:
                lines.append({"text": line.get("text", ""), "evidence": None, "missing": True})
        sections.append({"title": sec.get("title", ""), "lines": lines})

    artifact = Artifact(
        artifact_type="resume",
        title=f"简历·{req.direction}",
        content=json.dumps(sections, ensure_ascii=False),
        direction=req.direction,
        source_ids={"archive": [s.get("id") for s in profile_sections]},
        status="draft",
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)

    task.status = "success"
    task.progress = 100
    task.result = {"artifact_id": artifact.id, "version": artifact.version}
    task.steps = [{"step": "整理档案", "status": "done", "detail": f"已加载 {len(profile_sections)} 条"},
                  {"step": "AI 生成", "status": "done", "detail": "简历生成完成"}]
    await db.commit()

    return {
        "task_id": task.id,
        "artifact_id": artifact.id,
        "version": artifact.version,
        "direction": req.direction,
        "sections": sections,
        "gaps": out.get("gaps", []),
    }


@router.post("/resume/generate")
async def resume_generate(req: ResumeGenerateReq, db: AsyncSession = Depends(get_db)):
    """A2 一键简历（按方向定制，逐条证据链）——长任务，返回 task_id 可轮询"""
    if not req.direction.strip():
        raise HTTPException(400, "请指定简历方向")
    return await _run_resume_generate(db, req)


@router.get("/resume")
async def list_resumes(
    artifact_type: str | None = None,
    direction: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """简历/生成物列表（多方向多版本）"""
    query = select(Artifact).order_by(Artifact.created_at.desc())
    if artifact_type:
        query = query.where(Artifact.artifact_type == artifact_type)
    if direction:
        query = query.where(Artifact.direction == direction)
    result = await db.execute(query)
    items = result.scalars().all()
    return {
        "items": [
            {"artifact_id": a.id, "title": a.title, "version": a.version, "direction": a.direction,
             "status": a.status, "created_at": a.created_at.isoformat() if a.created_at else None}
            for a in items
        ],
        "total": len(items),
    }


@router.post("/resume/{artifact_id}/versions")
async def resume_new_version(
    artifact_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """换方向/换模板重生成 → 新版本（版本链 parent_artifact_id）"""
    parent = (await db.execute(select(Artifact).where(Artifact.id == artifact_id))).scalar_one_or_none()
    if not parent:
        raise HTTPException(404, "原生成物不存在")
    direction = payload.get("direction") or parent.direction
    template = payload.get("template") or ""
    source_ids = parent.source_ids or {}
    req = ResumeGenerateReq(direction=direction, archive_record_ids=source_ids.get("archive"), template=template)
    result = await _run_resume_generate(db, req)
    # 关联版本链
    new_artifact = (await db.execute(select(Artifact).where(Artifact.id == result["artifact_id"]))).scalar_one()
    new_artifact.parent_artifact_id = parent.id
    new_artifact.version = (parent.version or 1) + 1
    new_artifact.title = f"{new_artifact.title} v{new_artifact.version}"
    await db.commit()
    return {
        "new_artifact_id": new_artifact.id,
        "version": new_artifact.version,
        "parent_artifact_id": parent.id,
    }


# ================= A3 面试模拟 =================

@router.post("/interview/questions")
async def interview_questions(payload: dict, db: AsyncSession = Depends(get_db)):
    """A3 面试问题预测（≥8 题，基于真实经历带证据链）"""
    direction = payload.get("direction") or "保研-计算机"
    profile_sections, _ = await _collect_profile(db, payload.get("archive_record_ids"))
    out = await llm_service.interview_questions(direction, profile_sections)
    questions = out.get("questions", [])
    # related_record_id 校验：映射 profile 里的记录 id
    id_map = {f"rec{r['id']}": r["id"] for r in profile_sections} if any("id" in r for r in profile_sections) else {}
    for q in questions:
        q["related_record_id"] = q.get("related_record_id")
    return {"direction": direction, "questions": questions}


@router.post("/interview/feedback", response_model=FeedbackOut)
async def interview_feedback(req: InterviewFeedbackReq, db: AsyncSession = Depends(get_db)):
    """A3 模拟回答分维度点评"""
    if not req.qa_pairs:
        raise HTTPException(400, "请提供问答对")
    out = await llm_service.interview_feedback(req.direction, req.qa_pairs)
    return FeedbackOut(
        score=out.get("score") or {},
        feedback=out.get("feedback", ""),
        advice=out.get("advice", ""),
    )


# ================= 导出 =================

@router.post("/artifacts/{artifact_id}/export")
async def export_artifact(artifact_id: int, db: AsyncSession = Depends(get_db)):
    """简历/个人陈述导出 docx"""
    a = (await db.execute(select(Artifact).where(Artifact.id == artifact_id))).scalar_one_or_none()
    if not a:
        raise HTTPException(404, "生成物不存在")

    title = a.title or "生成物"
    blocks = []
    if a.artifact_type == "resume":
        try:
            sections = json.loads(a.content or "[]")
            for sec in sections:
                blocks.append({"type": "para", "text": f"【{sec.get('title', '')}】"})
                for line in sec.get("lines", []):
                    text = line.get("text", "")
                    if line.get("missing") or not line.get("text"):
                        text = (text + " 【待补充】").strip()
                    blocks.append({"type": "list", "items": [text]})
        except json.JSONDecodeError:
            blocks.append({"type": "para", "text": a.content})
    else:
        blocks.append({"type": "para", "text": a.content})

    try:
        filename = export_service.export_docx(title, blocks)
    except Exception as e:
        raise HTTPException(400, f"导出失败: {e}")
    return {"file_url": f"/api/files/{filename}", "filename": filename}


# ================= A5 保研/求职节点（S4 补） =================

# ================= 统一任务中心接入（S3b） =================
# 注册简历生成为 /api/tasks 可调用的 handler：fn(db, payload) -> dict

async def _resume_handler(db: AsyncSession, payload: dict) -> dict:
    req = ResumeGenerateReq(**{k: v for k, v in (payload or {}).items() if k in {"direction", "archive_record_ids", "template"}})
    return await _run_resume_generate(db, req)


task_service.register_handler("career.resume_generate", _resume_handler)


# ================= A5 保研/求职节点（S4 补） =================

@router.get("/milestones")
async def career_milestones(db: AsyncSession = Depends(get_db)):
    """保研/求职关键节点（来源角标 source_type=career 的待办；S4 补充日历联动）"""
    links = (await db.execute(select(TodoLink).where(TodoLink.source_type == "career"))).scalars().all()
    items = []
    for link in links:
        todo = (await db.execute(select(TodoItem).where(TodoItem.id == link.todo_id))).scalar_one_or_none()
        if todo:
            items.append({
                "id": link.id,
                "label": link.label or todo.content,
                "content": todo.content,
                "deadline": todo.deadline.isoformat() if todo.deadline else None,
                "status": todo.status.value if hasattr(todo.status, "value") else todo.status,
            })
    return {"items": items, "total": len(items)}
