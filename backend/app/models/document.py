"""政策文件、文档切片、版本差异模型"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, LargeBinary, Float
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf | docx | html
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    full_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    version = Column(Integer, default=1)
    previous_version_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    source_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    embedding = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class DocumentDiff(Base):
    __tablename__ = "document_diffs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    old_version_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    new_version_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    diff_type = Column(String(20), nullable=False)  # added | removed | modified
    section_title = Column(String(300), nullable=True)
    old_content = Column(Text, nullable=True)
    new_content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
