"""数据库连接和会话管理"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def init_db():
    """创建所有表（幂等：只建缺失表，绝不 ALTER 老表，ADR 000 §3）"""
    from app.models.notification import Notification
    from app.models.todo import TodoItem
    from app.models.exam import Exam
    from app.models.document import Document, DocumentChunk, DocumentDiff
    from app.models.document_tag import DocumentTag
    from app.models.archive_record import ArchiveRecord
    from app.models.artifact import Artifact
    from app.models.todo_link import TodoLink
    from app.models.task_progress import TaskProgress
    from app.models.paper import PaperMeta
    from app.models.signup import Signup, SignupEntry
    from app.models.ledger import LedgerEntry
    from app.models.audit_log import AuditLog
    from app.models.demo_seed import DemoSeed
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """获取数据库会话"""
    async with async_session_factory() as session:
        yield session
