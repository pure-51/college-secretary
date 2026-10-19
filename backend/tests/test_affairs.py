"""S3 回归：affairs 域（3 技能 + 路由端到端，MockLLM 离线确定性）
覆盖 ADR 契约：D1 通知生成 / D2 接龙去重+统计+导出+催办 / D3 台账脱敏。
"""
import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.services.skill_registry import registry
from app.services.llm_service import llm_service


# ============ 技能层（registry.run） ============

async def test_affairs_skills_registered():
    names = registry.list_skills()
    for n in ("affairs.notice", "affairs.signup_parse", "affairs.ledger_extract"):
        assert n in names


async def test_notice_draft_and_copy():
    out = await registry.run("affairs.notice", {"scene": "团建", "key_points": ["周六", "南门"], "tone": ""})
    assert "本周六下午2点" in out.draft
    assert "南门集合" in out.copy_text
    assert len(out.draft) > len(out.copy_text)  # 草稿完整版、copy 精简版


async def test_signup_parse_entries():
    out = await registry.run("affairs.signup_parse", {"raw_text": "1.张三 去 2.李四 不去"})
    assert len(out.entries) == 2
    assert out.entries[0].name == "张三"
    assert out.entries[0].option == "去"
    assert out.entries[1].detail is None


async def test_ledger_extract_amounts():
    out = await registry.run("affairs.ledger_extract", {"ocr_text": "烧烤材料150.5"})
    assert len(out.entries) == 2
    assert out.entries[0].amount == pytest.approx(-150.5)  # 支出为负
    assert out.entries[1].amount == 200  # 余额为正


async def test_affairs_llm_service_delegates():
    r = await llm_service.notice_generate("团建", ["周六"])
    assert r["draft"] != ""
    r = await llm_service.signup_parse("张三 去")
    assert r["entries"][0]["name"] == "张三"
    r = await llm_service.ledger_extract("材料150")
    assert r["entries"][0]["amount"] == pytest.approx(-150.5)


# ============ 路由端到端（TestClient） ============

@pytest.fixture
def client():
    with TestClient(main_app.app) as c:
        yield c


def test_notice_generate_endpoint(client):
    r = client.post("/api/affairs/notices/generate", json={"scene": "团建", "key_points": ["周六"]})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "南门集合" in data["copy_text"]
    assert "本周六下午2点" in data["draft"]


def test_signup_create_and_stats(client):
    r = client.post("/api/affairs/signups", json={"title": "周六团建", "options": ["去", "不去"]})
    assert r.status_code == 200
    sid = r.json()["id"]
    assert r.json()["status"] == "open"

    r = client.get(f"/api/affairs/signups/{sid}")
    assert r.status_code == 200
    stats = r.json()["stats"]
    # 契约冻结字段
    assert set(stats.keys()) == {"total", "unique", "per_option", "unsubmitted"}
    assert stats["total"] == 0


def test_signup_import_dedupe_override(client):
    r = client.post("/api/affairs/signups", json={"title": "接龙去重测试"})
    sid = r.json()["id"]

    # 首次导入 2 人
    r = client.post(f"/api/affairs/signups/{sid}/import", json={"raw_text": "1.张三 去 2.李四 不去"})
    assert r.status_code == 200
    assert r.json()["added"] == 2
    assert r.json()["updated"] == 0

    # 再次导入（Mock 固定返回 张三+李四 → 两人均已存在 → 覆盖式更新，不新增）
    r = client.post(f"/api/affairs/signups/{sid}/import", json={"raw_text": "1.张三 待定"})
    assert r.json()["added"] == 0
    assert r.json()["updated"] == 2

    stats = client.get(f"/api/affairs/signups/{sid}").json()["stats"]
    assert stats["unique"] == 2  # 去重后仍是 2 人


def test_signup_export_xlsx(client, tmp_path, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "EXPORT_DIR", tmp_path)
    r = client.post("/api/affairs/signups", json={"title": "导出测试"})
    sid = r.json()["id"]
    client.post(f"/api/affairs/signups/{sid}/import", json={"raw_text": "张三 去"})
    e = client.post(f"/api/affairs/signups/{sid}/export")
    assert e.status_code == 200
    url = e.json()["file_url"]
    assert client.get(url).status_code == 200


def test_signup_unsubmitted_todo(client):
    r = client.post("/api/affairs/signups", json={"title": "催办测试"})
    sid = r.json()["id"]
    client.post(f"/api/affairs/signups/{sid}/import", json={"raw_text": "张三 去"})
    r = client.post(f"/api/affairs/signups/{sid}/todo")
    assert r.status_code == 200
    assert r.json()["todo_id"]
    assert r.json()["submitted_count"] == 2  # Mock 固定解析出张三+李四 2 人


def test_ledger_import_and_export(client, tmp_path, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "EXPORT_DIR", tmp_path)
    r = client.post("/api/affairs/ledger/import", json={"ocr_text": "烧烤材料150.5 余额200"})
    assert r.status_code == 200
    assert r.json()["added"] == 2

    e = client.post("/api/affairs/ledger/export")
    assert e.status_code == 200
    assert e.json()["total"] == 2
    url = e.json()["file_url"]
    assert client.get(url).status_code == 200


def test_ledger_missing_document_rules(client):
    r = client.post("/api/affairs/signups/999/export")
    assert r.status_code == 404
    r = client.get("/api/affairs/signups/999")
    assert r.status_code == 404
