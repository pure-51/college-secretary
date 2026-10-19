"""S0-5 回归集：技能注册表 + 5 个已迁移技能（MockLLM 离线确定性验证）
覆盖：注册表装配 / schema 校验 / 缓存 / 模板渲染 / 未知技能 / 非法 JSON 回退 / 垫片转发。
"""
import pytest

from app.services.skill_registry import registry, SkillNotFoundError
from app.services.llm_service import llm_service

EXPECTED_SKILLS = [
    "affairs.ledger_extract",
    "affairs.notice",
    "affairs.signup_parse",
    "career.archive_extract",
    "career.interview_feedback",
    "career.interview_questions",
    "career.personal_statement",
    "career.resume_generate",
    "consult.chat_query",
    "documents.compare",
    "inbox.classify",
    "inbox.extract_exams",
    "inbox.extract_todos",
    "inbox.judge_relevance",
    "orchestrate.route",
    "papers.compare",
    "papers.explain",
    "papers.meta_extract",
    "papers.qa",
    "papers.review_section",
    "report.generate",
    "report.handle_chat",
    "retrieval.rerank",
    "summary.generate",
]


# ============ 注册表装配 ============

async def test_registry_has_five_skills():
    assert registry.list_skills() == sorted(EXPECTED_SKILLS)


async def test_each_skill_resolvable():
    for name in EXPECTED_SKILLS:
        skill = registry.get(name)
        assert skill is not None
        assert skill.name == name
        assert skill.system_prompt != ""  # prompt 已装配


async def test_unknown_skill_raises():
    with pytest.raises(SkillNotFoundError):
        await registry.run("nonexistent.task", {"x": 1})


# ============ inbox.classify ============

async def test_classify_returns_schema(mock_llm):
    out = await registry.run("inbox.classify", {"content": "关于四六级成绩的通知"})
    assert out.category == "教务"
    assert out.confidence == pytest.approx(0.92)
    assert "四六级" in out.reason


async def test_classify_renders_user_payload(mock_llm):
    await registry.run("inbox.classify", {"content": "任意内容XYZ"})
    user_msg = mock_llm.calls[0][1]["content"]
    assert "任意内容XYZ" in user_msg  # {{content}} 已替换


async def test_classify_llm_service_delegates():
    result = await llm_service.classify_message("四六级通知")
    assert isinstance(result, dict)
    assert result["category"] == "教务"


# ============ inbox.extract_todos ============

async def test_extract_todos_returns_list():
    out = await registry.run("inbox.extract_todos", {"content": "有三项待办"})
    assert isinstance(out.todos, list)
    assert len(out.todos) == 2
    assert out.todos[0].content == "提交推免材料"
    assert out.todos[0].location == "教务办公室"


async def test_extract_todos_missing_optional_fields_ok():
    out = await registry.run("inbox.extract_todos", {"content": "只有一条，无地点"})
    assert out.todos[1].location is None  # Mock 返回第二条无 location
    assert out.todos[1].deadline == "2026-08-12"


async def test_extract_todos_llm_service_returns_list_of_dict():
    result = await llm_service.extract_todos("处理待办")
    assert isinstance(result, list)
    assert result[0]["content"] == "提交推免材料"


# ============ inbox.extract_exams ============

async def test_extract_exams_schema():
    out = await registry.run("inbox.extract_exams", {"content": "补考安排"})
    assert len(out.exams) == 1
    e = out.exams[0]
    assert e.subject == "高等数学A补考"
    assert e.seat_number == "A12"


async def test_extract_exams_llm_service():
    result = await llm_service.extract_exams("考试通知")
    assert result[0]["subject"] == "高等数学A补考"


# ============ inbox.judge_relevance ============

async def test_judge_relevance_true():
    out = await registry.run("inbox.judge_relevance", {"content": "保研面试通知"})
    assert out.relevant is True
    assert "保研" in out.reason


async def test_judge_relevance_llm_service():
    result = await llm_service.judge_relevance("保研面试")
    assert result["relevant"] is True


# ============ summary.generate（纯文本，json_mode=False）============

async def test_summary_generate_returns_plain_text():
    out = await registry.run("summary.generate", {"content": "长文本", "max_length": 200})
    assert isinstance(out, str)
    assert "摘要技能" in out
    assert "{" not in out  # 不是 JSON 包装


async def test_summary_generate_llm_service():
    result = await llm_service.generate_summary("内容", max_length=100)
    assert isinstance(result, str) and len(result) > 0


# ============ 缓存与回退 ============

async def test_cache_hit_same_payload_no_second_call(mock_llm):
    payload = {"content": "完全相同的输入"}
    r1 = await registry.run("inbox.classify", payload)
    r2 = await registry.run("inbox.classify", payload)
    assert r1 is r2  # 命中缓存返回同一对象
    assert len(mock_llm.calls) == 1  # LLM 只被调一次


async def test_cache_miss_different_payload(mock_llm):
    await registry.run("inbox.classify", {"content": "输入A"})
    await registry.run("inbox.classify", {"content": "输入B"})
    assert len(mock_llm.calls) == 2


async def test_invalid_json_falls_back_to_defaults(mock_llm):
    mock_llm.text_mode = True  # 返回非 JSON
    out = await registry.run("inbox.classify", {"content": "触发非法JSON"})
    assert out.category == "其他"  # schema 默认值
    assert out.confidence == 0.0
    assert out.reason == "解析失败"


async def test_invalid_json_extract_todos_fallback(mock_llm):
    mock_llm.text_mode = True
    out = await registry.run("inbox.extract_todos", {"content": "x"})
    assert out.todos == []


# ============ 模板渲染健壮性 ============

async def test_render_user_strips_unresolved_placeholders(mock_llm):
    skill = registry.get("inbox.classify")
    rendered = registry.render_user(skill, {"content": "有值", "unused": 1})
    assert "{{" not in rendered  # 残留占位符被清理
    assert "有值" in rendered
