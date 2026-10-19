"""S4 回归：legacy 三域技能迁移 + 收件箱转档案联动
覆盖 ADR 契约：consult/report/documents 走 SkillRegistry（24 技能齐）/ confirm+archive 建 pending 档案。
"""
import io

import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.services.skill_registry import registry
from app.services.llm_service import llm_service


# ============ 技能层 ============

async def test_all_24_skills_registered():
    names = registry.list_skills()
    assert len(names) == 24  # inbox4+summary1+career5+papers5+affairs3+orchestrate2+legacy4
    for n in ("consult.chat_query", "report.generate", "report.handle_chat", "documents.compare"):
        assert n in names


async def test_legacy_llm_service_delegates():
    # 纯文本技能 → str
    r = await llm_service.chat_query("奖学金怎么评", "知识库")
    assert isinstance(r, str) and "奖学金" in r
    r = await llm_service.generate_report([{"content": "保研面试", "deadline": "9月10日"}], [], [1])
    assert isinstance(r, str) and "待办" in r
    # JSON 技能 → dict
    r = await llm_service.handle_report_chat(
        [{"role": "user", "content": "我完成保研面试了"}], [{"id": 1, "content": "保研面试"}], []
    )
    assert isinstance(r, dict) and r["actions"][0]["type"] == "complete_todo"
    r = await llm_service.compare_documents("旧版", "新版")
    assert isinstance(r, dict) and r["diffs"][0]["type"] == "modified"


# ============ 路由端到端 ============

@pytest.fixture
def client():
    with TestClient(main_app.app) as c:
        yield c


def test_consult_endpoint_returns_answer(client):
    # 先建文档切片（关键词搜索命中才走 LLM chat_query）
    # ai_consult 用空格分词匹配整词：文档切片须含完整查询词
    client.post("/api/knowledge/documents", files={
        "file": ("policy.txt", io.BytesIO("奖学金怎么评 奖学金评审办法 综合学业成绩与综合测评".encode("utf-8")), "text/plain"),
    })
    r = client.post("/api/ai/consult", json={"question": "奖学金怎么评"})
    assert r.status_code == 200
    assert "奖学金" in r.json()["answer"]


def test_report_generate_endpoint(client):
    r = client.post("/api/ai/report")
    assert r.status_code == 200
    assert "待办" in r.json()["report"]  # 迁移后走 report.generate 技能，行为不变


def test_inbox_confirm_archive_creates_record(client):
    # 导入消息 → AI 处理
    before = client.get("/api/career/archive-records").json()["total"]
    r = client.post("/api/inbox/messages", json={"source_type": "text", "raw_content": "国家奖学金拟推荐名单通知"})
    mid = r.json()["id"]

    # confirm + archive=true → 建 pending 档案（相对计数，兼容共享临时库）
    r = client.put(f"/api/inbox/messages/{mid}/confirm", json={"archive": True})
    assert r.status_code == 200
    assert r.json()["archived"] is True

    records = client.get("/api/career/archive-records").json()
    assert records["total"] == before + 1
    assert records["items"][0]["record_status"] == "pending"


def test_inbox_confirm_without_archive_no_record(client):
    before = client.get("/api/career/archive-records").json()["total"]
    r = client.post("/api/inbox/messages", json={"source_type": "text", "raw_content": "四六级成绩通知"})
    mid = r.json()["id"]
    r = client.put(f"/api/inbox/messages/{mid}/confirm", json={})
    assert r.json()["archived"] is False
    after = client.get("/api/career/archive-records").json()["total"]
    assert after == before  # 不带 archive 不新建档案
