"""考试安排模型"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.database import Base

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=True)
    subject = Column(String(200), nullable=False)
    exam_time = Column(DateTime, nullable=False)
    location = Column(String(200), nullable=True)
    seat_number = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    source_original = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
