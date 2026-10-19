"""待办事项模型"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum
from app.database import Base
import enum

class TodoStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TodoItem(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=True)
    content = Column(Text, nullable=False)
    deadline = Column(DateTime, nullable=True)
    location = Column(String(200), nullable=True)
    status = Column(SAEnum(TodoStatus), default=TodoStatus.PENDING)
    source_original = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
