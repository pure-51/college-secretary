"""演示数据管理（ADR 000 §4：seed/clear/demo-status，数据 owner）
clear 只删 demo_seeds 登记行，不污染正式数据。
"""
from fastapi import APIRouter
from sqlalchemy import select, func

from app.database import async_session_factory
from app.seed_data import seed_demo, clear_demo
from app.services.demo_mode import is_demo
from app.models import Notification, TodoItem, Document, ArchiveRecord, Artifact, Signup, DemoSeed

router = APIRouter(prefix="/api/admin", tags=["管理"])

_COUNT_MODELS = [
    ("notifications", Notification),
    ("todos", TodoItem),
    ("documents", Document),
    ("archive_records", ArchiveRecord),
    ("artifacts", Artifact),
    ("signups", Signup),
]


@router.post("/seed")
async def admin_seed():
    result = await seed_demo()
    return {"ok": True, **result}


@router.post("/clear")
async def admin_clear():
    await clear_demo()
    return {"ok": True, "demo_mode": False}


@router.get("/demo-status")
async def demo_status():
    async with async_session_factory() as db:
        counts = {}
        for name, model in _COUNT_MODELS:
            counts[name] = (await db.execute(select(func.count(model.id)))).scalar_one()
        # seeded 语义：demo_seeds 登记表是否还有行（而非 notification>0，避免真实数据误判）
        seeded = (await db.execute(select(func.count(DemoSeed.id)))).scalar_one() > 0
    return {"demo_mode": is_demo(), "seeded": seeded, "counts": counts}
