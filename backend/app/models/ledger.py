"""台账条目模型（D3，ADR 000 §3.9）"""
import datetime
from sqlalchemy import Column, Integer, String, Date, Float, DateTime, ForeignKey
from app.database import Base

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=True)
    item = Column(String(300), nullable=True)
    amount = Column(Float, nullable=True)  # 原始金额（仅本地存储）
    amount_masked = Column(String(30), nullable=True)  # 展示值 如 "¥***"
    category = Column(String(50), nullable=True)
    evidence_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    status = Column(String(20), default="pending")  # pending|approved|rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
