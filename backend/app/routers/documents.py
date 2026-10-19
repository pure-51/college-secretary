"""知识库 API - 文件上传/检索/问答/版本对比"""
import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.document import Document, DocumentChunk, DocumentDiff
from app.services.llm_service import llm_service
from app.services.document_parser import DocumentParser
from app.utils.file_storage import save_uploaded_file
from app.utils.text_utils import split_into_chunks
from pydantic import BaseModel

router = APIRouter()
doc_parser = DocumentParser()

@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """上传政策文件（PDF/Word/HTML）"""
    filepath = await save_uploaded_file(await file.read(), file.filename or "doc")
    ext = Path(file.filename).suffix.lower() if file.filename else ".bin"

    # 解析文档
    full_text = await doc_parser.parse(filepath)

    doc_title = title or file.filename or "未命名文档"
    file_size = Path(filepath).stat().st_size

    # 检查是否已有同名文件（版本检测）
    existing = await db.execute(
        select(Document).where(Document.title == doc_title).order_by(Document.version.desc())
    )
    prev_doc = existing.scalar_one_or_none()
    version = (prev_doc.version + 1) if prev_doc else 1

    # 创建文档记录
    document = Document(
        title=doc_title,
        file_type=ext.replace(".", ""),
        file_path=str(filepath),
        file_size=file_size,
        full_text=full_text,
        version=version,
        previous_version_id=prev_doc.id if prev_doc else None,
        created_at=datetime.datetime.utcnow(),
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # 生成摘要
    summary = await llm_service.generate_summary(full_text[:3000])
    document.summary = summary

    # 切片 + 生成向量嵌入
    chunks = split_into_chunks(full_text)
    for chunk in chunks:
        doc_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=chunk["index"],
            content=chunk["content"],
            page_number=chunk.get("page"),
            created_at=datetime.datetime.utcnow(),
        )
        db.add(doc_chunk)

    # 版本对比
    if prev_doc:
        diff = await llm_service.compare_documents(prev_doc.full_text[:5000], full_text[:5000])
        for d in diff.get("diffs", []):
            doc_diff = DocumentDiff(
                old_version_id=prev_doc.id,
                new_version_id=document.id,
                diff_type=d.get("type", "modified"),
                section_title=d.get("section"),
                summary=d.get("summary"),
                created_at=datetime.datetime.utcnow(),
            )
            db.add(doc_diff)

    document.updated_at = datetime.datetime.utcnow()
    await db.commit()
    await db.refresh(document)

    return {
        "id": document.id,
        "title": document.title,
        "file_type": document.file_type,
        "version": document.version,
        "summary": document.summary,
        "page_count": document.page_count,
        "size": file_size,
    }

@router.get("/documents")
async def list_documents(
    search: str = Query(None),
    file_type: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取文件列表"""
    query = select(Document).order_by(Document.created_at.desc())
    if search:
        query = query.where(Document.full_text.ilike(f"%{search}%"))
    if file_type:
        query = query.where(Document.file_type == file_type)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": d.id,
                "title": d.title,
                "file_type": d.file_type,
                "version": d.version,
                "summary": d.summary,
                "page_count": d.page_count,
                "file_size": d.file_size,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in items
        ],
        "total": len(items),
    }

@router.get("/documents/{doc_id}")
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    """获取文件详情"""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "文件不存在")

    return {
        "id": doc.id,
        "title": doc.title,
        "file_type": doc.file_type,
        "full_text": doc.full_text,
        "summary": doc.summary,
        "version": doc.version,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    """删除文件"""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "文件不存在")

    # 删除关联的切片和差异记录
    await db.execute(DocumentChunk.__table__.delete().where(DocumentChunk.document_id == doc_id))  # type: ignore
    await db.execute(DocumentDiff.__table__.delete().where(
        or_(DocumentDiff.old_version_id == doc_id, DocumentDiff.new_version_id == doc_id)
    ))  # type: ignore
    await db.delete(doc)
    await db.commit()

    return {"status": "deleted"}

@router.get("/search")
async def search_knowledge(
    q: str = Query(..., description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
):
    """全文搜索知识库"""
    query = select(DocumentChunk).join(Document).where(
        DocumentChunk.content.ilike(f"%{q}%")
    ).limit(20)
    result = await db.execute(query)
    chunks = result.scalars().all()

    # 获取关联的文档信息
    doc_ids = {c.document_id for c in chunks}
    docs_result = await db.execute(select(Document).where(Document.id.in_(doc_ids)))
    docs = {d.id: d for d in docs_result.scalars().all()}

    return {
        "results": [
            {
                "document_id": c.document_id,
                "title": docs[c.document_id].title if c.document_id in docs else "未知",
                "content": c.content[:500],
                "page": c.page_number,
            }
            for c in chunks
        ],
        "total": len(chunks),
    }

@router.get("/documents/{doc_id}/versions")
async def get_versions(doc_id: int, db: AsyncSession = Depends(get_db)):
    """获取版本历史"""
    diffs_result = await db.execute(
        select(DocumentDiff).where(
            or_(DocumentDiff.old_version_id == doc_id, DocumentDiff.new_version_id == doc_id)
        ).order_by(DocumentDiff.created_at.desc())
    )
    diffs = diffs_result.scalars().all()

    return {
        "diffs": [
            {
                "type": d.diff_type,
                "section": d.section_title,
                "summary": d.summary,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in diffs
        ]
    }

class CompareRequest(BaseModel):
    doc_id_old: int
    doc_id_new: int

@router.post("/compare")
async def compare_documents(
    request: CompareRequest,
    db: AsyncSession = Depends(get_db),
):
    """对比两个版本的文件"""
    old = await db.execute(select(Document).where(Document.id == request.doc_id_old))
    new = await db.execute(select(Document).where(Document.id == request.doc_id_new))
    old_doc = old.scalar_one_or_none()
    new_doc = new.scalar_one_or_none()

    if not old_doc or not new_doc:
        raise HTTPException(404, "文件不存在")

    diff = await llm_service.compare_documents(
        old_doc.full_text[:5000] or "",
        new_doc.full_text[:5000] or "",
    )

    return {
        "old_title": old_doc.title,
        "new_title": new_doc.title,
        "overall_summary": diff.get("overall_summary", ""),
        "diffs": diff.get("diffs", []),
    }


@router.delete("/documents")
async def clear_all_documents(db: AsyncSession = Depends(get_db)):
    """清空所有文档"""
    await db.execute(DocumentDiff.__table__.delete())
    await db.execute(DocumentChunk.__table__.delete())
    await db.execute(Document.__table__.delete())
    await db.commit()
    return {"status": "cleared"}
