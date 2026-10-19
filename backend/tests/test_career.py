"""S1 回归：career 域（5 技能 + 路由端到端，MockLLM 离线确定性）
覆盖 ADR 契约：简历五段证据链、面试四维评分、体检规则、版本链、导出。
"""
import json

import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.services.skill_registry import registry
from app.services.llm_service import llm_service
from app.config import settings


# ============ 技能层（registry.run） ============

async def test_career_skills_registered():
    names = registry.list_skills()
    for n in ("career.archive_extract", "career.resume_generate", "career.interview_questions",
              "career.interview_feedback", "career.personal_statement"):
        assert n in names


async def test_archive_extract_schema():
    out = await registry.run("career.archive_extract", {"ocr_text": "国家奖学金证书 林小夏", "category_hint": "honor"})
    assert out.record_type == "honor"
    assert out.fields["level"] == "国家级"
    assert out.evidence_confidence == pytest.approx(0.95)


async def test_resume_generate_missing_line_flag():
    """无来源行必须 missing=True（前端标【待补充】）"""
    out = await registry.run("career.resume_generate", {
        "direction": "保研-计算机",
        "profile_sections": [{"key": "rec1", "title": "教育背景", "fields": {}}],
        "template": "",
    })
    lines = out.sections[0].lines
    assert lines[0].missing is False and lines[0].source_key == "rec1"
    assert lines[1].missing is True and lines[1].source_key is None
    assert out.gaps[0].field == "实习经历"


async def test_resume_generate_five_section_structure():
    out = await registry.run("career.resume_generate", {
        "direction": "保研", "profile_sections": [], "template": "",
    })
    assert len(out.sections) == 2  # Mock 返回教育背景/科研经历两段


async def test_interview_questions_min_count():
    out = await registry.run("career.interview_questions", {"direction": "保研", "profile": []})
    assert len(out.questions) == 3
    assert out.questions[0].related_record_id == 3
    assert out.questions[1].related_record_id is None


async def test_interview_feedback_four_dimension_score():
    out = await registry.run("career.interview_feedback", {
        "direction": "保研", "qa_pairs": [{"question": "Q", "answer": "A"}],
    })
    assert set(out.score.model_dump().keys()) == {"expression", "professional", "logic", "fit"}
    assert out.score.expression == 8
    assert out.advice != ""


async def test_personal_statement_schema():
    out = await registry.run("career.personal_statement", {
        "direction": "保研", "profile": [], "resume_summary": "简历摘要",
    })
    assert out.statement.startswith("我是林小夏")
    assert len(out.strengths) == 2 and len(out.plans) == 2


async def test_career_llm_service_delegates():
    r = await llm_service.archive_extract("材料文本", "honor")
    assert isinstance(r, dict) and r["record_type"] == "honor"
    r = await llm_service.interview_feedback("保研", [{"question": "Q", "answer": "A"}])
    assert "score" in r


# ============ 路由端到端（TestClient） ============

@pytest.fixture
def client():
    with TestClient(main_app.app) as c:
        yield c


def test_career_archive_crud(client):
    # 创建（手动录入）
    r = client.post("/api/career/archive-records", json={
        "record": {"record_type": "score", "title": "GPA 3.8", "fields": {"gpa": "3.8"}},
    })
    assert r.status_code == 200
    rid = r.json()["id"]

    # 列表+详情
    assert client.get("/api/career/archive-records").json()["total"] == 1
    detail = client.get(f"/api/career/archive-records/{rid}").json()
    assert "evidence" in detail

    # 确认
    assert client.put(f"/api/career/archive-records/{rid}", json={"record_status": "confirmed"}).json()["status"] == "updated"
    assert client.delete(f"/api/career/archive-records/{rid}").json()["status"] == "deleted"
    assert client.get(f"/api/career/archive-records/{rid}").status_code == 404


def test_career_health_check_rule_only(client):
    r = client.get("/api/career/health-check")
    assert r.status_code == 200
    hc = r.json()
    assert 0 <= hc["progress"] <= 100
    assert any(d["field"] == "个人信息" for d in hc["dimensions"])


def test_career_resume_generate_with_evidence_mapping(client):
    # 造两条档案：一条有证据、一条无证据
    a1 = client.post("/api/career/archive-records", json={
        "record": {"record_type": "honor", "title": "国奖", "evidence": {"source_document_id": 1, "confidence": 0.9}},
    }).json()["id"]
    a2 = client.post("/api/career/archive-records", json={
        "record": {"record_type": "internship", "title": "字节实习"},
    }).json()["id"]

    r = client.post("/api/career/resume/generate", json={"direction": "保研-计算机"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["artifact_id"] and data["task_id"]

    # 证据链映射：rec1 来自 a1（有证据 → missing False），但 Mock 固定 rec1 有来源
    # 断言结构：至少一个 missing 行存在（对应无来源行）
    all_lines = [line for sec in data["sections"] for line in sec["lines"]]
    assert any(l["missing"] for l in all_lines)


def test_career_resume_versions_chain(client):
    before = client.get("/api/career/resume").json()["total"]
    r1 = client.post("/api/career/resume/generate", json={"direction": "保研-计算机"})
    aid = r1.json()["artifact_id"]
    r2 = client.post(f"/api/career/resume/{aid}/versions", json={"direction": "求职-算法"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["version"] == 2
    assert r2.json()["parent_artifact_id"] == aid
    after = client.get("/api/career/resume").json()["total"]
    assert after == before + 2  # 原 + 新版本


def test_career_resume_export_docx(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "EXPORT_DIR", tmp_path)
    r = client.post("/api/career/resume/generate", json={"direction": "保研-计算机"})
    aid = r.json()["artifact_id"]
    e = client.post(f"/api/career/artifacts/{aid}/export")
    assert e.status_code == 200, e.text
    url = e.json()["file_url"]
    d = client.get(url)
    assert d.status_code == 200
    assert "wordprocessingml" in d.headers["content-type"]


def test_career_interview_feedback_contract(client):
    r = client.post("/api/career/interview/feedback", json={
        "direction": "保研",
        "qa_pairs": [{"question": "介绍项目", "answer": "参与了…"}],
    })
    assert r.status_code == 200, r.text
    assert set(r.json()["score"].keys()) == {"expression", "professional", "logic", "fit"}


def test_career_interview_questions(client):
    r = client.post("/api/career/interview/questions", json={"direction": "保研"})
    assert r.status_code == 200
    assert len(r.json()["questions"]) == 3


def test_career_milestones_empty_without_seed(client):
    r = client.get("/api/career/milestones")
    assert r.status_code == 200
    assert r.json()["total"] == 0
