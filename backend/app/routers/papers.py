"""科研论文库 API（B 域，ADR 000 §4：8 端点）
B1 论文上传 → 元数据抽取 → B2 通俗讲解（长任务）→ B3 单篇问答 → B4 多篇对比（P1）→ B5 综述生成（P1 长任务）
长任务策略：同步阻塞执行（裁决#10），同时写 task_progress 供前端轮询展示进度。
"""
import json
import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.models.paper import PaperMeta
from app.models.artifact import Artifact
from app.models.task_progress import TaskProgress
from app.schemas.papers import PaperMetaUpdate, PaperQAReq, PaperCompareReq, PaperReviewReq
from app.services.llm_service import llm_service
from app.services.document_parser import DocumentParser
from app.utils.file_storage import save_uploaded_file
from app.utils.text_utils import split_into_chunks

router = APIRouter(prefix="/api/papers", tags=["科研论文库"])
doc_parser = DocumentParser()


async def _get_document(db: AsyncSession, document_id: int) -> Document:
    doc = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "文档不存在")
    return doc


async def _get_paper_meta(db: AsyncSession, document_id: int) -> PaperMeta | None:
    return (await db.execute(select(PaperMeta).where(PaperMeta.document_id == document_id))).scalar_one_or_none()


async def _document_sections_text(db: AsyncSession, document_id: int) -> str:
    """论文正文分片拼接（供讲解/综述使用）"""
    chunks = (await db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
    )).scalars().all()
    if chunks:
        return "\n".join(c.content for c in chunks)
    doc = await _get_document(db, document_id)
    return doc.full_text or ""


async def _create_task(db: AsyncSession, skill_name: str, step: str) -> TaskProgress:
    task = TaskProgress(skill_name=skill_name, status="running", progress=10,
                        steps=[{"step": step, "status": "running", "detail": "AI 处理中"}])
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def _finish_task(db: AsyncSession, task: TaskProgress, result: dict):
    task.status = "success"
    task.progress = 100
    task.result = result
    for s in task.steps or []:
        s["status"] = "done"
    await db.commit()


# ================= B1 论文上传 =================

@router.post("/upload")
async def upload_paper(
    file: UploadFile = File(...),
    title: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """B1 上传论文（PDF/Word/文本）→ 存文档 + 切片 + 自动抽取题录"""
    filepath = await save_uploaded_file(await file.read(), file.filename or "paper.bin")
    ext = Path(file.filename).suffix.lower() if file.filename else ".bin"
    full_text = await doc_parser.parse(filepath)

    doc_title = title or file.filename or "未命名论文"
    document = Document(
        title=doc_title,
        file_type=ext.replace(".", ""),
        file_path=str(filepath),
        file_size=Path(filepath).stat().st_size,
        full_text=full_text,
        version=1,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # 切片
    chunks = split_into_chunks(full_text)
    for chunk in chunks:
        db.add(DocumentChunk(
            document_id=document.id,
            chunk_index=chunk["index"],
            content=chunk["content"],
            page_number=chunk.get("page"),
        ))
    await db.commit()

    # 元数据抽取
    meta = await llm_service.paper_meta_extract(full_text)
    paper = PaperMeta(
        document_id=document.id,
        title=meta.get("title"),
        authors=meta.get("authors"),
        journal=meta.get("journal"),
        year=meta.get("year"),
        doi=meta.get("doi"),
        abstract=meta.get("abstract"),
        language=meta.get("language", "en"),
        meta_status="auto",
    )
    db.add(paper)
    await db.commit()
    await db.refresh(paper)

    return {
        "document_id": document.id,
        "meta_id": paper.id,
        "title": paper.title or doc_title,
        "journal": paper.journal,
        "year": paper.year,
        "meta_status": paper.meta_status,
    }


# ================= 文献库列表 =================

@router.get("")
async def list_papers(
    search: str | None = None,
    journal: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """文献库列表（含题录与文档摘要）"""
    query = select(PaperMeta).join(Document).order_by(PaperMeta.updated_at.desc(), PaperMeta.created_at.desc())
    if search:
        query = query.where(Document.full_text.ilike(f"%{search}%"))
    if journal:
        query = query.where(PaperMeta.journal == journal)
    items = (await db.execute(query)).scalars().all()
    return {
        "items": [
            {
                "meta_id": p.id,
                "document_id": p.document_id,
                "title": p.title,
                "authors": p.authors,
                "journal": p.journal,
                "year": p.year,
                "doi": p.doi,
                "language": p.language,
                "meta_status": p.meta_status,
            }
            for p in items
        ],
        "total": len(items),
    }


# ================= B2 通俗讲解（长任务） =================

@router.post("/{document_id}/explain")
async def explain_paper(document_id: int, payload: dict | None = None, db: AsyncSession = Depends(get_db)):
    """B2 论文通俗讲解（分步骤，带来源切片）——长任务，返回 task_id 可轮询"""
    doc = await _get_document(db, document_id)
    meta = await _get_paper_meta(db, document_id)
    question = (payload or {}).get("question") or ""
    sections_text = await _document_sections_text(db, document_id)

    task = await _create_task(db, "papers.explain", "AI 讲解中")
    try:
        out = await llm_service.paper_explain(doc.title, meta.meta_to_dict() if meta else {}, sections_text, question)
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        await db.commit()
        raise HTTPException(502, f"讲解生成失败: {e}")

    parts = out.get("parts", [])
    artifact = Artifact(
        artifact_type="explain",
        title=f"论文讲解·{doc.title}",
        content=json.dumps(parts, ensure_ascii=False),
        source_ids={"document": [document_id]},
        status="draft",
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)
    await _finish_task(db, task, {"artifact_id": artifact.id, "parts": parts})

    return {"task_id": task.id, "artifact_id": artifact.id, "parts": parts}


# ================= B3 单篇问答 =================

@router.post("/{document_id}/ask")
async def ask_paper(document_id: int, req: PaperQAReq, db: AsyncSession = Depends(get_db)):
    """B3 单篇论文问答（带来源引用）"""
    doc = await _get_document(db, document_id)
    context = await _document_sections_text(db, document_id)
    out = await llm_service.paper_qa(req.question, context, req.history)
    return {
        "document_id": document_id,
        "answer": out.get("answer", ""),
        "citations": out.get("citations", []),
    }


# ================= 题录人工补录 =================

@router.put("/meta/{document_id}")
async def update_paper_meta(document_id: int, req: PaperMetaUpdate, db: AsyncSession = Depends(get_db)):
    """题录人工补录/修正（meta_status → manual）"""
    doc = await _get_document(db, document_id)
    paper = await _get_paper_meta(db, document_id)
    data = req.model_dump(exclude_none=True)
    if paper is None:
        paper = PaperMeta(document_id=document_id, meta_status="manual")
        db.add(paper)
    else:
        for key, value in data.items():
            setattr(paper, key, value)
        paper.meta_status = "manual"
    paper.updated_at = datetime.datetime.utcnow()
    await db.commit()
    await db.refresh(paper)
    return {"meta_id": paper.id, "document_id": document_id, "meta_status": paper.meta_status}


# ================= B4 多篇对比（P1） =================

@router.post("/compare")
async def compare_papers(req: PaperCompareReq, db: AsyncSession = Depends(get_db)):
    """B4 多篇论文维度对比"""
    if not req.document_ids:
        raise HTTPException(400, "请选择至少 1 篇论文")
    papers = []
    for doc_id in req.document_ids:
        doc = await _get_document(db, doc_id)
        meta = await _get_paper_meta(db, doc_id)
        papers.append({
            "id": doc_id,
            "title": (meta.title if meta and meta.title else doc.title),
            "meta": meta.meta_to_dict() if meta else {},
            "sections": await _document_sections_text(db, doc_id),
        })
    out = await llm_service.papers_compare(papers, req.dimensions)
    return {"table": out.get("table", {"columns": [], "rows": []})}


# ================= B5 综述生成（P1 长任务） =================

@router.post("/review/generate")
async def generate_review(req: PaperReviewReq, db: AsyncSession = Depends(get_db)):
    """B5 综述生成（分章节，逐句引用）——长任务，返回 task_id 可轮询"""
    if not req.document_ids:
        raise HTTPException(400, "请选择至少 1 篇论文")
    if not req.sections:
        req.sections = ["研究背景", "核心方法", "主要结论", "研究展望"]

    # 收集论文摘要
    summaries = []
    for doc_id in req.document_ids:
        doc = await _get_document(db, doc_id)
        meta = await _get_paper_meta(db, doc_id)
        summaries.append({
            "id": doc_id,
            "title": (meta.title if meta and meta.title else doc.title),
            "abstract": (meta.abstract if meta and meta.abstract else (doc.full_text or "")[:500]),
        })

    task = await _create_task(db, "papers.review_section", "AI 综述撰写中")
    sections = []
    citations = []
    try:
        for i, section in enumerate(req.sections):
            task.progress = 20 + int(i / max(len(req.sections), 1) * 70)
            await db.commit()
            out = await llm_service.paper_review_section(section, summaries, citations)
            sections.append({"title": section, "content": out.get("content", "")})
            citations.extend(out.get("citations", []))
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        await db.commit()
        raise HTTPException(502, f"综述生成失败: {e}")

    artifact = Artifact(
        artifact_type="review",
        title=f"文献综述·{len(req.document_ids)}篇",
        content=json.dumps(sections, ensure_ascii=False),
        source_ids={"documents": req.document_ids},
        status="draft",
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)
    await _finish_task(db, task, {"artifact_id": artifact.id, "citations": citations})

    return {"task_id": task.id, "artifact_id": artifact.id, "sections": sections, "citations": citations}


# ================= 综述查看/存回知识库 =================

@router.get("/review/{artifact_id}")
async def get_review(artifact_id: int, db: AsyncSession = Depends(get_db)):
    """综述查看（可存回知识库：写入 documents 表生成正式文档）"""
    a = (await db.execute(select(Artifact).where(Artifact.id == artifact_id))).scalar_one_or_none()
    if not a:
        raise HTTPException(404, "综述不存在")
    try:
        sections = json.loads(a.content or "[]")
    except json.JSONDecodeError:
        sections = []
    return {
        "artifact_id": a.id,
        "title": a.title,
        "sections": sections,
        "status": a.status,
    }
