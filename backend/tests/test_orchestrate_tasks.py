"""S3b 回归：统一调度（orchestrate 路由 + tasks 长任务中心 + rerank 精排）
覆盖 ADR 契约：意图路由六域枚举 / /api/tasks 创建轮询 / rerank 阈值（>5 走 LLM，否则保序）。
"""
import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.services.skill_registry import registry
from app.services.llm_service import llm_service
from app.services import retrieval_service, task_service


# ============ 技能层 ============

async def test_s3b_skills_registered():
    names = registry.list_skills()
    assert "orchestrate.route" in names
    assert "retrieval.rerank" in names


async def test_route_domain_enum():
    out = await registry.run("orchestrate.route", {"query": "帮我写保研简历", "context": ""})
    assert out.domain in {"career", "papers", "affairs", "schedule", "inbox", "assistant"}
    assert out.task == "career.resume_generate"


async def test_rerank_schema():
    out = await registry.run("retrieval.rerank", {"query": "q", "candidates": [{"id": 1, "title": "a", "content": "b"}]})
    assert len(out.ranked) == 2
    assert out.ranked[0].id == 2
    assert out.ranked[0].score == pytest.approx(0.95)


# ============ 服务层 ============

async def test_rerank_threshold_below_keeps_order():
    cands = [{"id": i, "title": f"doc{i}", "content": "x"} for i in range(1, 4)]
    r = await retrieval_service.rerank("query", cands)
    assert [c["id"] for c in r] == [1, 2, 3]  # ≤5 保序
    assert r[0]["score"] == pytest.approx(1.0)


async def test_rerank_threshold_above_uses_llm():
    cands = [{"id": i, "title": f"doc{i}", "content": "x"} for i in range(1, 7)]
    r = await retrieval_service.rerank("query", cands)
    assert r[0]["id"] == 2  # Mock LLM 精排把 id2 排第一
    assert len(r) == 6


async def test_rerank_empty():
    assert await retrieval_service.rerank("q", []) == []


# ============ 路由端到端 ============

@pytest.fixture
def client():
    with TestClient(main_app.app) as c:
        yield c


def test_orchestrate_endpoint(client):
    r = client.post("/api/ai/orchestrate", json={"query": "帮我写保研简历"})
    assert r.status_code == 200
    data = r.json()
    assert data["domain"] == "career"
    assert data["task"] == "career.resume_generate"
    # 契约冻结字段齐全
    assert set(data.keys()) == {"domain", "task", "params", "reply", "needs_clarification", "evidence"}


def test_tasks_create_poll_success(client):
    r = client.post("/api/tasks", json={"skill": "career.resume_generate", "payload": {"direction": "保研-计算机"}})
    assert r.status_code == 200
    tid = r.json()["task_id"]

    d = client.get(f"/api/tasks/{tid}").json()
    assert d["status"] == "success"
    assert d["progress"] == 100
    assert d["result"]["artifact_id"]


def test_tasks_unknown_skill_400(client):
    r = client.post("/api/tasks", json={"skill": "nonexistent.task", "payload": {}})
    assert r.status_code == 400


def test_tasks_missing_404(client):
    assert client.get("/api/tasks/99999").status_code == 404


def test_tasks_cancel_and_redo(client):
    r = client.post("/api/tasks", json={"skill": "career.resume_generate", "payload": {"direction": "保研-计算机"}})
    tid = r.json()["task_id"]
    # 已完成任务 cancel 标记后仍可 redo
    c = client.post(f"/api/tasks/{tid}/cancel")
    assert c.status_code == 200
    assert c.json()["status"] in ("success", "cancelled")
    rr = client.post(f"/api/tasks/{tid}/redo")
    assert rr.status_code == 200
    assert rr.json()["task_id"] != tid


def test_resume_handler_registered():
    assert task_service.has_handler("career.resume_generate")
