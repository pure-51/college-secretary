"""S0-5 测试基座：MockLLM（离线确定性）注入全局 registry + 临时 sqlite 库
关键点：
- MockLLM 按 system prompt 特征词匹配技能，返回确定性 JSON/纯文本，零网络、零依赖。
- 注入方式：直接替换 registry.llm_client（模块级单例的 llm_client 字段）。
- 每个测试前清空缓存，避免 TTL 缓存跨用例串扰。
"""
import os
import asyncio
from pathlib import Path

# 必须在导入 app 之前设置临时库路径（app.database 在模块加载时读 DATABASE_URL）
import tempfile

_tmp_dir = tempfile.mkdtemp(prefix="s0_test_")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{Path(_tmp_dir) / 'test.db'}"
os.environ["ENABLE_TOKEN"] = "false"  # 测试环境关闭 token，专注逻辑回归

import pytest
import pytest_asyncio

from app.services.skill_registry import registry
from app.services import skills as _skills  # noqa: F401  触发 register_all()
from app.services.cache_service import TTLCache


class MockLLM:
    """按 system prompt 特征词返回确定性输出（离线、可复现）"""

    def __init__(self):
        self.calls: list[dict] = []  # 记录调用 messages，供断言
        self.text_mode = False  # 置 True 时返回非 JSON，测 schema 回退默认值

    async def call(self, messages, temperature=0.1, max_tokens=2048, json_mode=False, retry=None):
        self.calls.append(messages)
        system = messages[0]["content"] if messages else ""
        if self.text_mode:
            return "这不是合法JSON，用来测回退默认值"

        if "消息分类器" in system:
            return '{"category": "教务", "confidence": 0.92, "reason": "涉及四六级成绩通知"}'
        if "待办事项提取器" in system:
            return '{"todos": [{"content": "提交推免材料", "deadline": "2026-09-10", "location": "教务办公室"}, {"content": "实验室报到", "deadline": "2026-08-12"}]}'
        if "考试信息提取器" in system:
            return '{"exams": [{"subject": "高等数学A补考", "exam_time": "2026-09-18 14:00", "location": "理科楼203", "seat_number": "A12"}]}'
        if "相关性判断器" in system:
            return '{"relevant": true, "reason": "保研面试与用户直接相关"}'
        if "摘要生成器" in system:
            return "这是一段用于验证摘要技能的确定性返回文本。"
        if "生涯档案" in system:
            return '{"record_type": "honor", "title": "国家奖学金", "fields": {"award": "国家奖学金", "level": "国家级"}, "evidence_confidence": 0.95}'
        if "简历撰写" in system:
            return '{"sections": [{"title": "教育背景", "lines": [{"text": "示例大学计算机科学与技术", "source_key": "rec1", "missing": false}, {"text": "无来源行", "source_key": null, "missing": true}]}, {"title": "科研经历", "lines": [{"text": "参与图像识别项目", "source_key": "rec2", "missing": false}]}], "gaps": [{"field": "实习经历", "suggestion": "补充实习材料"}]}'
        if "面试官" in system:
            return '{"questions": [{"question": "介绍你的科研项目", "focus": "项目深挖", "related_record_id": 3}, {"question": "谈谈职业规划", "focus": "规划", "related_record_id": null}, {"question": "为什么选择我们", "focus": "动机", "related_record_id": null}]}'
        if "面试点评官" in system:
            return '{"score": {"expression": 8, "professional": 7, "logic": 6, "fit": 8}, "feedback": "回答较完整，专业性强", "advice": "加强逻辑链"}'
        if "申请文书" in system:
            return '{"statement": "我是林小夏，示例大学计算机科学与技术专业…", "strengths": ["科研扎实", "编程能力强"], "plans": ["保研深造", "进入实验室研究图像识别"]}'
        if "元数据抽取专家" in system:
            return '{"title": "Deep Residual Learning for Image Recognition", "authors": "Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun", "journal": "CVPR", "year": 2016, "doi": null, "abstract": "提出残差网络解决深度网络退化问题。", "language": "en"}'
        if "科普讲解员" in system:
            return '{"parts": [{"title": "研究背景", "content": "深层网络难以训练是核心难题", "source_chunk_id": 1}, {"title": "核心方法", "content": "引入残差连接，让网络学习残差", "source_chunk_id": 2}]}'
        if "学术问答助手" in system:
            return '{"answer": "残差网络通过跳跃连接解决梯度消失", "citations": [{"chunk_id": 2, "confidence": 0.9}]}'
        if "文献对比专家" in system:
            return '{"table": {"columns": ["维度", "ResNet", "VGG"], "rows": [["方法", "残差连接", "深层堆叠"], ["结论", "更深网络可训练", "越深越难"] ]}}'
        if "综述撰写专家" in system:
            return '{"content": "深度学习在图像识别领域取得突破，其中残差网络代表性工作引入跳跃连接。", "citations": [{"document_id": 1, "quote": "残差网络"}]}'
        if "班委通知撰写专家" in system:
            return '{"draft": "【通知】关于本周六团建活动的安排\\n各位同学：\\n本周六下午2点南门集合，前往校园烧烤区团建。请准时参加。\\nXX班委 2026-08-10", "copy_text": "【通知】周六下午2点南门集合团建"}'
        if "接龙名单解析专家" in system:
            return '{"entries": [{"name": "张三", "detail": "班长", "option": "去"}, {"name": "李四", "detail": null, "option": "不去"}]}'
        if "班费台账记账专家" in system:
            return '{"entries": [{"date": "2026-08-01", "item": "团建烧烤材料", "amount": -150.5, "category": "餐饮"}, {"date": null, "item": "班费余额", "amount": 200, "category": "其他"}]}'
        if "意图路由专家" in system:
            return '{"domain": "career", "task": "career.resume_generate", "params": {"direction": "保研-计算机"}, "reply": "", "needs_clarification": false, "evidence": []}'
        if "检索精排专家" in system:
            return '{"ranked": [{"id": 2, "score": 0.95, "reason": "直接相关"}, {"id": 1, "score": 0.6, "reason": "部分相关"}]}'
        if "知识库回答问题的AI助手" in system:
            return "根据资料，奖学金评审需要综合学业成绩与综合测评。"
        if "贴心的AI大学生秘书" in system:
            return "今日待办2项：保研面试（9月10日）最紧急，请提前准备。另注意实验室报到培训。"
        if "任务管理AI" in system:
            return '{"reply": "好的，已为你完成该待办。", "actions": [{"type": "complete_todo", "id": 1}]}'
        if "政策文件对比专家" in system:
            return '{"diffs": [{"type": "modified", "section": "奖学金", "summary": "评审比例调整"}], "overall_summary": "评审细则有微调"}'
        if json_mode:
            return '{"error": "未知技能"}' if json_mode else ""
        return "未知技能"


@pytest_asyncio.fixture(autouse=True)
async def _mock_llm_and_cleanup():
    """自动注入 MockLLM + 清空缓存；结束后复位 llm_client 避免污染其他测试文件"""
    _mock = MockLLM()
    original = registry.llm_client
    registry.llm_client = _mock
    registry.cache = TTLCache(ttl=600)  # 每个测试独立缓存
    yield
    registry.llm_client = original


@pytest.fixture
def mock_llm() -> MockLLM:
    """获取当前注入的 MockLLM 实例（断言 calls / text_mode）"""
    return registry.llm_client
