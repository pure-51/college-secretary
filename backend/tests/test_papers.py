"""S2 回归：papers 域（5 技能 + 路由端到端，MockLLM 离线确定性）
覆盖 ADR 契约：B1 上传→题录抽取 / B2 通俗讲解（长任务）/ B3 问答引用 / B4 对比表 / B5 综述。
"""
import io

import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.services.skill_registry import registry
from app.services.llm_service import llm_service


# ============ 技能层（registry.run） ============

async def test_papers_skills_registered():
    names = registry.list_skills()
    for n in ("papers.meta_extract", "papers.explain", "papers.qa", "papers.compare", "papers.review_section"):
        assert n in names


async def test_meta_extract_schema():
    out = await registry.run("papers.meta_extract", {"full_text_first_3000": "Deep Residual Learning..."})
    assert out.title == "Deep Residual Learning for Image Recognition"
    assert out.year == 2016
    assert out.language == "en"


async def test_meta_extract_truncates_long_input():
    out = await registry.run("papers.meta_extract", {"full_text_first_3000": "x" * 5000})
    assert out.journal == "CVPR"  # Mock 分支命中即验证调用链完整


async def test_explain_parts_with_source_chunk():
    out = await registry.run("papers.explain", {
        "title": "ResNet", "meta": {}, "sections_text": "正文", "question": "",
    })
    assert len(out.parts) == 2
    assert out.parts[0].source_chunk_id == 1


async def test_qa_with_citations():
    out = await registry.run("papers.qa", {"question": "为什么残差有效", "context": "上下文", "history": []})
    assert "梯度消失" in out.answer
    assert out.citations[0].chunk_id == 2


async def test_compare_table_structure():
    out = await registry.run("papers.compare", {"papers": [{"title": "A"}], "dimensions": []})
    assert out.table["columns"][0] == "维度"
    assert len(out.table["rows"]) == 2


async def test_review_section_content_and_citations():
    out = await registry.run("papers.review_section", {
        "section": "引言", "papers_summaries": [{"id": 1}], "citations": [],
    })
    assert "残差网络" in out.content
    assert out.citations[0].document_id == 1


async def test_papers_llm_service_delegates():
    r = await llm_service.paper_meta_extract("论文正文")
    assert r["year"] == 2016
    r = await llm_service.papers_compare([{"title": "A"}])
    assert "columns" in r["table"]
    r = await llm_service.paper_review_section("引言", [{"id": 1}])
    assert r["content"] != ""


# ============ 路由端到端（TestClient） ============

@pytest.fixture
def client():
    with TestClient(main_app.app) as c:
        yield c


def _upload_pdf(client, name="paper.pdf"):
    """构造一个假 PDF 内容上传（document_parser 解析 PDF 时会尝试 fitz 失败 → 回退原文）"""
    content = b"Deep Residual Learning for Image Recognition. %PDF fake content"
    return client.post("/api/papers/upload", files={"file": (name, io.BytesIO(content), "application/pdf")})


def test_papers_upload_and_meta(client):
    r = _upload_pdf(client)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["document_id"]
    assert data["title"] == "Deep Residual Learning for Image Recognition"
    assert data["year"] == 2016
    assert data["meta_status"] == "auto"


def test_papers_list(client):
    _upload_pdf(client)
    r = client.get("/api/papers")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    item = r.json()["items"][0]
    assert item["journal"] == "CVPR"
    assert item["meta_status"] == "auto"
    assert item["document_id"]  # 关联文档存在


def test_papers_explain_long_task(client):
    doc_id = _upload_pdf(client).json()["document_id"]
    r = client.post(f"/api/papers/{doc_id}/explain", json={"question": "讲一下核心方法"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["task_id"] and data["artifact_id"]
    assert len(data["parts"]) == 2
    assert data["parts"][0]["source_chunk_id"] == 1


def test_papers_ask_with_citation(client):
    doc_id = _upload_pdf(client).json()["document_id"]
    r = client.post(f"/api/papers/{doc_id}/ask", json={"question": "为什么残差有效"})
    assert r.status_code == 200
    data = r.json()
    assert "梯度消失" in data["answer"]
    assert data["citations"][0]["chunk_id"] == 2


def test_papers_meta_manual_update(client):
    doc_id = _upload_pdf(client).json()["document_id"]
    r = client.put(f"/api/papers/meta/{doc_id}", json={"journal": "TPAMI", "year": 2026})
    assert r.status_code == 200
    assert r.json()["meta_status"] == "manual"
    # 列表验证更新生效
    item = client.get("/api/papers").json()["items"][0]
    assert item["journal"] == "TPAMI"


def test_papers_compare_endpoint(client):
    id1 = _upload_pdf(client, "p1.pdf").json()["document_id"]
    id2 = _upload_pdf(client, "p2.pdf").json()["document_id"]
    r = client.post("/api/papers/compare", json={"document_ids": [id1, id2], "dimensions": ["方法"]})
    assert r.status_code == 200, r.text
    assert r.json()["table"]["columns"][1] == "ResNet"


def test_papers_review_generate(client):
    doc_id = _upload_pdf(client).json()["document_id"]
    r = client.post("/api/papers/review/generate", json={"document_ids": [doc_id], "sections": ["研究背景"]})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["artifact_id"]
    assert data["sections"][0]["title"] == "研究背景"
    # 综述查看
    r2 = client.get(f"/api/papers/review/{data['artifact_id']}")
    assert r2.status_code == 200
    assert len(r2.json()["sections"]) == 1


def test_papers_missing_document_404(client):
    assert client.post("/api/papers/999/explain", json={}).status_code == 404
    assert client.post("/api/papers/999/ask", json={"question": "q"}).status_code == 404
    assert client.put("/api/papers/meta/999", json={"journal": "X"}).status_code == 404
