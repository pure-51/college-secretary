"""S0-5 模型契约回归：16 模型类 + 表名 + 关键列 + 幂等建表（临时库）"""
import pytest

from app.database import Base, init_db


async def test_all_models_registered():
    """Base.metadata 已注册 ADR §3 的全部新表（含旧表，共 17 张）"""
    from app.models import (
        Notification, TodoItem, Exam, Document, DocumentChunk, DocumentDiff,
        DocumentTag, ArchiveRecord, Artifact, TodoLink, TaskProgress,
        PaperMeta, Signup, SignupEntry, LedgerEntry, AuditLog, DemoSeed,
    )
    tables = set(Base.metadata.tables.keys())
    expected = {
        "notifications", "todos", "exams", "documents", "document_chunks",
        "document_diffs", "document_tags", "archive_records", "artifacts",
        "todo_links", "task_progress", "papers_meta", "signups",
        "signup_entries", "ledger_entries", "audit_logs", "demo_seeds",
    }
    assert expected <= tables  # 契约表全部存在（可多不可少）


async def test_demo_seed_columns():
    from app.models import DemoSeed
    cols = {c.name for c in DemoSeed.__table__.columns}
    assert {"run_id", "table_name", "row_id"} <= cols


async def test_paper_meta_columns():
    from app.models import PaperMeta
    cols = {c.name for c in PaperMeta.__table__.columns}
    assert {"document_id", "title", "authors", "year", "abstract", "meta_status"} <= cols


async def test_audit_log_metadata_column():
    """规避保留名：属性 metadata_，库列名 metadata（ADR §3）"""
    from app.models import AuditLog
    cols = {c.name for c in AuditLog.__table__.columns}
    assert "metadata" in cols
    assert hasattr(AuditLog, "metadata_")


async def test_signup_models():
    from app.models import Signup, SignupEntry
    assert Signup.__tablename__ == "signups"
    assert SignupEntry.__tablename__ == "signup_entries"
    entry_cols = {c.name for c in SignupEntry.__table__.columns}
    assert {"signup_id", "name", "option", "is_duplicate"} <= entry_cols


async def test_ledger_columns():
    from app.models import LedgerEntry
    cols = {c.name for c in LedgerEntry.__table__.columns}
    assert "amount" in cols


async def test_archive_record_evidence():
    from app.models import ArchiveRecord
    cols = {c.name for c in ArchiveRecord.__table__.columns}
    assert {"evidence_document_id", "evidence_confidence", "sensitivity", "record_status"} <= cols


async def test_todo_link_columns():
    from app.models import TodoLink
    cols = {c.name for c in TodoLink.__table__.columns}
    assert {"todo_id", "source_type", "source_id", "label"} <= cols


async def test_init_db_idempotent():
    """init_db 幂等：重复调用不报错（ADR §3 无 Alembic 硬约束）"""
    await init_db()
    await init_db()


async def test_document_tables():
    from app.models import Document, DocumentChunk, DocumentTag
    assert Document.__tablename__ == "documents"
    assert DocumentChunk.__tablename__ == "document_chunks"
    assert DocumentTag.__tablename__ == "document_tags"


async def test_notification_legacy_table_untouched():
    """旧表零改动：notifications 表名与列保持原样（ADR §3 冻结）"""
    from app.models import Notification
    assert Notification.__tablename__ == "notifications"
    cols = {c.name for c in Notification.__table__.columns}
    assert {"raw_content", "category", "relevance", "status"} <= cols
