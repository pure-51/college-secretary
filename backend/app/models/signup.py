"""接龙模型（D2，ADR 000 §3.7-3.8）"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy import JSON
from app.database import Base

class Signup(Base):
    __tablename__ = "signups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    options = Column(JSON, nullable=True)  # 如 ["去","不去","待定"]
    deadline = Column(DateTime, nullable=True)
    status = Column(String(20), default="open")  # open | closed
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SignupEntry(Base):
    __tablename__ = "signup_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signup_id = Column(Integer, ForeignKey("signups.id"), nullable=False)
    name = Column(String(100), nullable=False)
    detail = Column(String(300), nullable=True)
    option = Column(String(100), nullable=True)
    source = Column(String(20), default="text")  # text|image|manual
    source_notification_id = Column(Integer, nullable=True)
    is_duplicate = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (UniqueConstraint("signup_id", "name", name="uq_signup_entry_name"),)
