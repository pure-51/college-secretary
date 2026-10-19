"""演示种子追踪模型（clear 唯一依据，ADR 000 §3.11）"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class DemoSeed(Base):
    __tablename__ = "demo_seeds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=False)
    row_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
