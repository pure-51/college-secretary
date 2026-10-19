"""S0-5 端到端编排回归：seed → demo-status → 幂等 seed → clear → 导出（TestClient 真实请求）"""
import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.config import settings


@pytest.fixture
def client():
    with TestClient(main_app.app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_seed_ok(client):
    r = client.post("/api/admin/seed")
    assert r.status_code == 200
    seeded = r.json()["seeded"]
    assert seeded["inbox"] == 6
    assert seeded["papers"] == 4
    assert seeded["archive"] == 5
    assert seeded["signups"] == 1


def test_seed_idempotent(client):
    """幂等：第二次 seed 不报 UNIQUE 冲突（S0-4 修复点）"""
    assert client.post("/api/admin/seed").status_code == 200
    r2 = client.post("/api/admin/seed")
    assert r2.status_code == 200


def test_demo_status_after_seed(client):
    client.post("/api/admin/seed")
    s = client.get("/api/admin/demo-status")
    assert s.status_code == 200
    assert s.json()["demo_mode"] is True
    assert s.json()["seeded"] is True


def test_clear_removes_seed_data(client):
    client.post("/api/admin/seed")
    c = client.post("/api/admin/clear")
    assert c.status_code == 200
    s = client.get("/api/admin/demo-status")
    assert s.json()["demo_mode"] is False
    assert s.json()["seeded"] is False
    # seed 数据清零，但不影响真实库（本测试为临时库）
    assert s.json()["counts"]["documents"] == 0


def test_export_docx_roundtrip(client, tmp_path, monkeypatch):
    """导出 docx → 下载文件（防穿越由 files 路由负责）"""
    monkeypatch.setattr(settings, "EXPORT_DIR", tmp_path)
    r = client.post("/api/export/docx", json={
        "title": "周报",
        "blocks": [
            {"type": "para", "text": "本周完成收件箱处理"},
            {"type": "list", "items": ["保研材料", "实验室报到"]},
        ],
    })
    assert r.status_code == 200
    file_url = r.json()["file_url"]
    assert file_url.startswith("/api/files/")
    d = client.get(file_url)
    assert d.status_code == 200
    assert d.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.wordprocessingml")


def test_export_xlsx_roundtrip(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "EXPORT_DIR", tmp_path)
    r = client.post("/api/export/xlsx", json={
        "headers": ["姓名", "成绩"],
        "rows": [["林小夏", "564"]],
    })
    assert r.status_code == 200
    file_url = r.json()["file_url"]
    d = client.get(file_url)
    assert d.status_code == 200


def test_files_path_traversal_blocked(client, tmp_path, monkeypatch):
    """路径穿越被拦截（404 或 403 均可，防穿越生效即通过）"""
    monkeypatch.setattr(settings, "EXPORT_DIR", tmp_path)
    for evil in ("../secrets.env", "%2e%2e/secrets.env", "..%2F..%2Fetc%2Fpasswd"):
        r = client.get(f"/api/files/{evil}")
        assert r.status_code in (403, 404)
