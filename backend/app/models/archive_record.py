"""生涯档案记录模型（A 域核心，ADR 000 §3.2）"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy import JSON
from app.database import Base

class ArchiveRecord(Base):
    __tablename__ = "archive_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # honor|score|internship|activity|skill|paper_meta|ledger|signup_row|certificate
    record_type = Column(String(50), nullable=False)
    title = Column(String(300), nullable=True)
    fields = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    # 证据链契约（显式列，Evidence{source_document_id, chunk_id, page, confidence}）
    evidence_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    evidence_chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=True)
    evidence_page = Column(Integer, nullable=True)
    evidence_confidence = Column(Float, nullable=True)
    sensitivity = Column(String(20), default="internal")  # public | internal | sensitive
    record_status = Column(String(20), default="pending")  # pending | confirmed | rejected
    source_notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
