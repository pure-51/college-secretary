"""操作审计模型（P1，ADR 000 §3.10）"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import JSON
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)  # 只记元数据，不存正文；列名保持 metadata（ADR §3.10）
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
