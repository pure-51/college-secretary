"""待办来源角标模型（todos 老表不改动，ADR 000 §3.4）"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class TodoLink(Base):
    __tablename__ = "todo_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    todo_id = Column(Integer, ForeignKey("todos.id"), nullable=False)
    # inbox|career|affairs|signup|activity
    source_type = Column(String(30), nullable=False)
    source_id = Column(Integer, nullable=True)
    label = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
