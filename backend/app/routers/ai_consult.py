"""AI 咨询 API - 基于知识库的政策问答"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.document import DocumentChunk, Document
from app.services.llm_service import llm_service
from pydantic import BaseModel

router = APIRouter()

class ConsultRequest(BaseModel):
    question: str

@router.post("/consult")
async def consult(
    request: ConsultRequest,
    db: AsyncSession = Depends(get_db),
):
    """用户提问，AI从知识库中检索并回答"""
    question = request.question.strip()
    if not question:
        raise HTTPException(400, "请输入问题")

    # 简单关键词搜索（Phase 1 本地版）
    # 将问题拆成关键词
    keywords = [w for w in question.replace("？", " ").replace("？", " ").split() if len(w) > 1]

    # 搜索匹配的文档切片
    matching_chunks = []
    for kw in keywords[:5]:  # 最多用5个关键词
        result = await db.execute(
            select(DocumentChunk).join(Document).where(
                DocumentChunk.content.ilike(f"%{kw}%")
            ).limit(10)
        )
        matching_chunks.extend(result.scalars().all())

    # 去重
    seen_ids = set()
    unique_chunks = []
    for c in matching_chunks:
        if c.id not in seen_ids:
            seen_ids.add(c.id)
            unique_chunks.append(c)

    if not unique_chunks:
        return {
            "answer": "抱歉，我在知识库中没有找到与你的问题相关的信息。请尝试换个关键词或上传相关文件。",
            "sources": [],
        }

    # 构建上下文
    context_parts = []
    sources = []
    for chunk in unique_chunks[:5]:  # 最多用5个切片
        # 获取文档标题
        doc_result = await db.execute(select(Document).where(Document.id == chunk.document_id))
        doc = doc_result.scalar_one_or_none()
        doc_title = doc.title if doc else "未知文档"

        context_parts.append(f"[来源: {doc_title}]\n{chunk.content[:2000]}")
        sources.append({
            "document_id": chunk.document_id,
            "title": doc_title,
            "content": chunk.content[:300],
        })

    context = "\n\n---\n\n".join(context_parts)

    # AI 回答
    answer = await llm_service.chat_query(question, context)

    return {
        "answer": answer,
        "sources": sources,
    }
