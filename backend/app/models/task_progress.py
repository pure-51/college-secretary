"""长任务进度模型（唯一表结构，ADR 000 §3.5）"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy import JSON
from app.database import Base

class TaskProgress(Base):
    __tablename__ = "task_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_name = Column(String(100), nullable=False)
    status = Column(String(20), default="running")  # running|success|failed|cancelled
    steps = Column(JSON, nullable=True)
    progress = Column(Integer, default=0)  # 0-100
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
