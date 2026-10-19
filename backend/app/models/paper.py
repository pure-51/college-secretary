"""论文题录模型（B 域，ADR 000 §3.6）"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.database import Base

class PaperMeta(Base):
    __tablename__ = "papers_meta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), unique=True, nullable=False)
    title = Column(String(500), nullable=True)
    authors = Column(String(500), nullable=True)
    journal = Column(String(200), nullable=True)
    year = Column(Integer, nullable=True)
    doi = Column(String(200), nullable=True)
    abstract = Column(Text, nullable=True)
    language = Column(String(20), default="en")
    meta_status = Column(String(20), default="auto")  # auto|manual|missing
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

    def meta_to_dict(self) -> dict:
        """题录字段字典（供技能/路由拼接）"""
        return {
            "title": self.title,
            "authors": self.authors,
            "journal": self.journal,
            "year": self.year,
            "doi": self.doi,
            "abstract": self.abstract,
            "language": self.language,
        }
