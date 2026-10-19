"""生成物模型（版本链，ADR 000 §3.3）"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy import JSON
from app.database import Base

class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # resume|personal_statement|review|explain|notice
    artifact_type = Column(String(50), nullable=False)
    title = Column(String(300), nullable=True)
    content = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    parent_artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=True)
    direction = Column(String(100), nullable=True)
    source_ids = Column(JSON, nullable=True)
    export_path = Column(String(500), nullable=True)
    status = Column(String(20), default="draft")  # draft | final
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
