"""通知/消息模型"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum as SAEnum
from app.database import Base
import enum

class RelevanceEnum(str, enum.Enum):
    PENDING = "pending"
    RELEVANT = "relevant"
    IRRELEVANT = "irrelevant"

class StatusEnum(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String(20), nullable=False)  # text | image | link
    raw_content = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    category = Column(String(50), nullable=True)
    category_confidence = Column(Float, nullable=True)
    relevance = Column(SAEnum(RelevanceEnum), default=RelevanceEnum.PENDING)
    status = Column(SAEnum(StatusEnum), default=StatusEnum.PENDING)
    user_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
