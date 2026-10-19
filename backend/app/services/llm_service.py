"""LLM API 调用封装（ADR 000 §1：技能注册表为唯一 LLM 底座）
全部技能已迁移 → SkillRegistry.run（薄委托垫片，调用方行为不变）。
"""
# 触发技能注册表装配（skills/__init__ 的 register_all）
from app.services import skills as _skills  # noqa: F401
from app.services.skill_registry import registry

class LLMService:
    # ================= 已迁移：薄委托垫片 =================

    async def classify_message(self, content: str) -> dict:
        """将消息分类为：教务/学工/社团/其他"""
        out = await registry.run("inbox.classify", {"content": content})
        return out.model_dump()

    async def extract_todos(self, content: str) -> list[dict]:
        """从消息中提取待办事项"""
        out = await registry.run("inbox.extract_todos", {"content": content})
        return out.model_dump().get("todos", [])

    async def extract_exams(self, content: str) -> list[dict]:
        """从消息/图片文字中提取考试安排信息"""
        out = await registry.run("inbox.extract_exams", {"content": content})
        return out.model_dump().get("exams", [])

    async def judge_relevance(self, content: str) -> dict:
        """判断消息是否与用户相关"""
        out = await registry.run("inbox.judge_relevance", {"content": content})
        return out.model_dump()

    async def generate_summary(self, content: str, max_length: int = 300) -> str:
        """生成摘要"""
        return await registry.run("summary.generate", {"content": content, "max_length": max_length})

    # ================= S1 迁移：career 域薄委托垫片 =================

    async def archive_extract(self, ocr_text: str, category_hint: str = "") -> dict:
        """材料 OCR 文本 → 结构化档案字段（A1）"""
        out = await registry.run("career.archive_extract", {"ocr_text": ocr_text, "category_hint": category_hint})
        return out.model_dump()

    async def resume_generate(self, direction: str, profile_sections: list, template: str = "") -> dict:
        """定制简历逐条证据链生成（A2 Hero）"""
        out = await registry.run("career.resume_generate", {
            "direction": direction,
            "profile_sections": profile_sections,
            "template": template,
        })
        return out.model_dump()

    async def interview_questions(self, direction: str, profile: list) -> dict:
        """面试问题预测（A3）"""
        out = await registry.run("career.interview_questions", {"direction": direction, "profile": profile})
        return out.model_dump()

    async def interview_feedback(self, direction: str, qa_pairs: list) -> dict:
        """面试回答分维度点评（A3）"""
        out = await registry.run("career.interview_feedback", {"direction": direction, "qa_pairs": qa_pairs})
        return out.model_dump()

    async def personal_statement(self, direction: str, profile: list, resume_summary: str) -> dict:
        """个人陈述/申请材料生成（A4 P1）"""
        out = await registry.run("career.personal_statement", {
            "direction": direction,
            "profile": profile,
            "resume_summary": resume_summary,
        })
        return out.model_dump()

    # ================= S2 迁移：papers 域薄委托垫片 =================

    async def paper_meta_extract(self, full_text: str) -> dict:
        """论文正文前部 → 题录元数据（B1）"""
        out = await registry.run("papers.meta_extract", {"full_text_first_3000": full_text[:3000]})
        return out.model_dump()

    async def paper_explain(self, title: str, meta: dict, sections_text: str, question: str = "") -> dict:
        """论文通俗讲解（B2 长任务）"""
        out = await registry.run("papers.explain", {
            "title": title,
            "meta": meta,
            "sections_text": sections_text,
            "question": question,
        })
        return out.model_dump()

    async def paper_qa(self, question: str, context: str, history: list = None) -> dict:
        """单篇论文问答（B3）"""
        out = await registry.run("papers.qa", {
            "question": question,
            "context": context,
            "history": history or [],
        })
        return out.model_dump()

    async def papers_compare(self, papers: list, dimensions: list = None) -> dict:
        """多篇论文维度对比（B4 P1）"""
        out = await registry.run("papers.compare", {"papers": papers, "dimensions": dimensions or []})
        return out.model_dump()

    async def paper_review_section(self, section: str, papers_summaries: list, citations: list = None) -> dict:
        """综述章节撰写（B5 P1 长任务）"""
        out = await registry.run("papers.review_section", {
            "section": section,
            "papers_summaries": papers_summaries,
            "citations": citations or [],
        })
        return out.model_dump()

    # ================= S3 迁移：affairs 域薄委托垫片 =================

    async def notice_generate(self, scene: str, key_points: list, tone: str = "") -> dict:
        """班级通知生成（D1）"""
        out = await registry.run("affairs.notice", {"scene": scene, "key_points": key_points, "tone": tone})
        return out.model_dump()

    async def signup_parse(self, raw_text: str) -> dict:
        """接龙名单解析（D2）"""
        out = await registry.run("affairs.signup_parse", {"raw_text": raw_text})
        return out.model_dump()

    async def ledger_extract(self, ocr_text: str) -> dict:
        """班费台账提取（D3 P1）"""
        out = await registry.run("affairs.ledger_extract", {"ocr_text": ocr_text})
        return out.model_dump()

    # ================= S3b 迁移：统一调度薄委托垫片 =================

    async def route_intent(self, query: str, context: str = "") -> dict:
        """统一意图路由（ADR §4：domain 枚举 career|papers|affairs|schedule|inbox|assistant）"""
        out = await registry.run("orchestrate.route", {"query": query, "context": context})
        return out.model_dump()

    async def rerank(self, query: str, candidates: list) -> dict:
        """检索精排（ADR §7：候选 >5 触发 LLM 精排，否则按原序）"""
        out = await registry.run("retrieval.rerank", {"query": query, "candidates": candidates})
        return out.model_dump()

    # ================= S4 迁移：legacy 三域薄委托垫片 =================

    async def chat_query(self, question: str, context: str) -> str:
        """基于知识库回答问题（consult.chat_query，纯文本输出）"""
        return await registry.run("consult.chat_query", {"question": question, "context": context[:8000]})

    async def generate_report(self, todos: list, exams: list, notifications: list, completed_todos: list = None) -> str:
        """生成 AI 汇报（report.generate，纯文本输出）"""
        todo_text = "\n".join([f"- {t.get('content', '')} (截止: {t.get('deadline', '未设置')})" for t in todos]) or "暂无待办"
        exam_text = "\n".join([f"- {e.get('subject', '')} ({e.get('exam_time', '')} @ {e.get('location', '未定')})" for e in exams]) or "暂无考试"
        completed_text = ""
        if completed_todos:
            completed_text = "\n本周已完成:\n" + "\n".join([f"- ✅ {t.get('content', '')}" for t in completed_todos])
        return await registry.run("report.generate", {
            "todos": todo_text,
            "exams": exam_text,
            "notif_count": len(notifications),
            "completed_text": completed_text,
        })

    async def handle_report_chat(self, messages: list[dict], todos: list[dict], exams: list[dict]) -> dict:
        """处理对话意图并给出操作（report.handle_chat，JSON 输出）"""
        todo_text = "\n".join([f"  [ID:{t['id']}] {t['content']} (截止: {t.get('deadline', '未设')})" for t in todos]) or "  暂无待办"
        exam_text = "\n".join([f"  [ID:{e['id']}] {e['subject']} ({e.get('exam_time', '未定')})" for e in exams]) or "  暂无考试"
        history_text = "\n".join([
            f"{'用户' if m['role'] == 'user' else 'AI'}: {m['content']}"
            for m in messages[-6:]  # 最近6条
        ])
        out = await registry.run("report.handle_chat", {
            "todos": todo_text,
            "exams": exam_text,
            "history_text": history_text,
        })
        return out.model_dump()

    async def compare_documents(self, old_text: str, new_text: str) -> dict:
        """对比两个版本的政策文件（documents.compare，JSON 输出）"""
        out = await registry.run("documents.compare", {"old_text": old_text[:5000], "new_text": new_text[:5000]})
        return out.model_dump()

llm_service = LLMService()
