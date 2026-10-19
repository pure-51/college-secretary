"""文档标签模型（检索池隔离，ADR 000 §3.1）"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from app.database import Base

class DocumentTag(Base):
    __tablename__ = "document_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    tag = Column(String(50), nullable=False)  # policy | career | papers | affairs
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (UniqueConstraint("document_id", "tag", name="uq_document_tag"),)
