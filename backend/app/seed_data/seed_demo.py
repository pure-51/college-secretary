"""林小夏演示数据（ADR 000：六幕剧本 seed）
虚构脱敏人物：林小夏，示例大学 2022 级计算机科学与技术，保研+团支书+科研助理三合一。
seed 写正式表并逐行登记 demo_seeds（含全部附属行）；clear 只删登记行，绝不全表清空（ADR §3.11）。
"""
import datetime

from sqlalchemy import select, delete

from app.database import async_session_factory
from app.services.demo_mode import enable as _demo_enable, disable as _demo_disable
from app.models import (
    Notification,
    TodoItem,
    Exam,
    Document,
    DocumentChunk,
    DocumentTag,
    ArchiveRecord,
    Artifact,
    TodoLink,
    PaperMeta,
    Signup,
    SignupEntry,
    DemoSeed,
)

# clear 用：按 FK 依赖逆序（先删引用方），只删 demo_seeds 登记的行
_CLEAR_MODELS = [
    ("signup_entries", SignupEntry),
    ("papers_meta", PaperMeta),
    ("document_tags", DocumentTag),
    ("document_chunks", DocumentChunk),
    ("todo_links", TodoLink),
    ("artifacts", Artifact),
    ("archive_records", ArchiveRecord),
    ("signups", Signup),
    ("todos", TodoItem),
    ("exams", Exam),
    ("documents", Document),
    ("notifications", Notification),
]

_EXTRA_TABLE = {
    "DocumentTag": "document_tags",
    "DocumentChunk": "document_chunks",
    "PaperMeta": "papers_meta",
    "TodoLink": "todo_links",
}


def _now(days: int = 0) -> datetime.datetime:
    """保研节点等日期用相对偏移，避免硬编码过期"""
    return datetime.datetime.now() + datetime.timedelta(days=days)


async def seed_demo() -> dict:
    """加载林小夏全套数据并开启演示态；幂等（已 seed 则先按登记清旧再重建）"""
    run_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    counts = {"inbox": 0, "papers": 0, "archive": 0, "signups": 0, "todos": 0, "exams": 0}

    async with async_session_factory() as db:
        async with db.begin():
            # 幂等：已有 seed 数据先按登记回删
            old = (await db.execute(select(DemoSeed.id).limit(1))).scalar_one_or_none()
            if old is not None:
                await _delete_seeded_rows(db)

            def reg(table_name: str, row_id: int):
                db.add(DemoSeed(run_id=run_id, table_name=table_name, row_id=row_id))

            def reg_objs(objs):
                for o in objs:
                    reg(_EXTRA_TABLE[type(o).__name__], o.id)

            # ===== ① 收件箱 6 条 =====
            notifs = [
                Notification(source_type="text",
                             raw_content="关于公示2025-2026学年国家奖学金拟推荐名单的通知：经评审，林小夏同学拟推荐为国家奖学金候选人，公示期5天。",
                             category="学工", relevance="relevant", status="pending"),
                Notification(source_type="text",
                             raw_content="【四六级】林小夏同学2025年12月英语六级成绩：564分（通过）。",
                             category="教务", relevance="relevant", status="pending"),
                Notification(source_type="text",
                             raw_content="关于公布2026年推免生资格名单的通知：林小夏获得推免资格，面试定于9月10日进行。",
                             category="教务", relevance="relevant", status="pending"),
                Notification(source_type="text",
                             raw_content="【社团】软件学院ACM俱乐部周末迎新活动报名开始，本周六下午2点南门集合。",
                             category="社团", relevance="relevant", status="pending"),
                Notification(source_type="text",
                             raw_content="【失物招领】食堂一楼拾到蓝色水杯一个，请失主到值班室认领。",
                             category="其他", relevance="irrelevant", status="pending"),
                Notification(source_type="text",
                             raw_content="林小夏同学：您已被聘为实验室科研助理，请于本周五下午到实验室报到并参加培训。",
                             category="学工", relevance="relevant", status="pending"),
            ]
            db.add_all(notifs)
            await db.flush()
            for n in notifs:
                reg("notifications", n.id)
            counts["inbox"] = len(notifs)

            # 待办：科研助理报到 + 保研面试（来源=inbox，角标 via todo_links）
            todo1 = TodoItem(notification_id=notifs[2].id, content="参加保研面试（9月10日）", deadline=_now(30), status="pending")
            todo2 = TodoItem(notification_id=notifs[5].id, content="实验室科研助理报到培训", deadline=_now(3), status="pending")
            db.add_all([todo1, todo2])
            await db.flush()
            for t in [todo1, todo2]:
                reg("todos", t.id)
            inbox_links = [
                TodoLink(todo_id=todo1.id, source_type="inbox", source_id=notifs[2].id, label="保研"),
                TodoLink(todo_id=todo2.id, source_type="inbox", source_id=notifs[2].id, label="保研"),
            ]
            db.add_all(inbox_links)
            await db.flush()
            reg_objs(inbox_links)
            counts["todos"] += 2

            # ===== ⑤ 日程：考试 + 保研关键节点（A5，来源=career） =====
            exam1 = Exam(notification_id=None, subject="高等数学 A（补考）", exam_time=_now(40), location="中心校区 理科楼 203", seat_number="A12")
            db.add(exam1)
            await db.flush()
            reg("exams", exam1.id)
            counts["exams"] = 1

            node1 = TodoItem(content="提交保研夏令营申请材料", deadline=_now(7), status="pending")
            node2 = TodoItem(content="9月保研面试", deadline=_now(30), status="pending")
            db.add_all([node1, node2])
            await db.flush()
            for t in [node1, node2]:
                reg("todos", t.id)
            career_links = [
                TodoLink(todo_id=node1.id, source_type="career", source_id=None, label="保研节点"),
                TodoLink(todo_id=node2.id, source_type="career", source_id=None, label="保研节点"),
            ]
            db.add_all(career_links)
            await db.flush()
            reg_objs(career_links)
            counts["todos"] += 2

            # ===== ② 知识库：3 篇论文（papers 标签+题录）+ 1 篇政策（policy 标签） =====
            papers = [
                Document(title="Deep Learning for Image Recognition", file_type="pdf", file_path="seed/paper1.pdf",
                         full_text="Deep learning has revolutionized image recognition. Convolutional neural networks...",
                         summary="深度学习在图像识别中的应用综述", page_count=8),
                Document(title="Attention Mechanisms in NLP", file_type="pdf", file_path="seed/paper2.pdf",
                         full_text="Attention mechanisms allow models to focus on relevant parts of the input sequence...",
                         summary="NLP中的注意力机制研究", page_count=10),
                Document(title="Graph Neural Networks Overview", file_type="pdf", file_path="seed/paper3.pdf",
                         full_text="Graph neural networks extend deep learning to graph-structured data...",
                         summary="图神经网络综述", page_count=12),
            ]
            policy = Document(title="示例大学本科生奖学金评审办法（2025年修订）", file_type="pdf", file_path="seed/policy.pdf",
                              full_text="第一章 总则。第一条 为规范奖学金评审…", summary="奖学金评审条件与流程", page_count=6)
            db.add_all(papers + [policy])
            await db.flush()
            for p in papers:
                reg("documents", p.id)
            reg("documents", policy.id)
            extra_docs = []
            for p in papers:
                extra_docs.append(DocumentTag(document_id=p.id, tag="papers"))
                extra_docs.append(DocumentChunk(document_id=p.id, chunk_index=0, content=p.full_text[:2000], page_number=1))
                extra_docs.append(PaperMeta(document_id=p.id, title=p.title, authors="Zhang Wei et al.", journal="IEEE Access",
                                            year=2025, language="en", abstract="摘要：该论文研究…", meta_status="auto"))
            extra_docs.append(DocumentTag(document_id=policy.id, tag="policy"))
            extra_docs.append(DocumentChunk(document_id=policy.id, chunk_index=0, content=policy.full_text[:2000], page_number=1))
            db.add_all(extra_docs)
            await db.flush()
            reg_objs(extra_docs)
            counts["papers"] = len(papers) + 1

            # ===== ③ 档案 5 条（含证据链） =====
            cert_doc = Document(title="国家奖学金证书", file_type="pdf", file_path="seed/certificate.pdf",
                                full_text="国家奖学金证书 林小夏 2025年度", page_count=1)
            db.add(cert_doc)
            await db.flush()
            reg("documents", cert_doc.id)
            cert_tag = DocumentTag(document_id=cert_doc.id, tag="career")
            db.add(cert_tag)
            await db.flush()
            reg_objs([cert_tag])

            records = [
                ArchiveRecord(record_type="honor", title="国家奖学金",
                              fields={"award": "国家奖学金", "level": "国家级", "date": "2025-06"},
                              evidence_document_id=cert_doc.id, evidence_confidence=0.98,
                              sensitivity="internal", record_status="confirmed"),
                ArchiveRecord(record_type="score", title="GPA 3.8/4.0",
                              fields={"gpa": "3.8", "major": "计算机科学与技术"},
                              sensitivity="sensitive", record_status="confirmed"),
                ArchiveRecord(record_type="internship", title="字节跳动算法实习生",
                              fields={"company": "字节跳动", "role": "算法实习生", "period": "2025.07-2025.10"},
                              sensitivity="internal", record_status="confirmed"),
                ArchiveRecord(record_type="honor", title="ACM 区域赛银奖",
                              fields={"award": "ACM-ICPC 区域赛银奖", "level": "国家级"},
                              sensitivity="public", record_status="confirmed"),
                ArchiveRecord(record_type="paper_meta", title="论文 2 篇收录",
                              fields={"papers": ["Deep Learning for Image Recognition", "Attention Mechanisms in NLP"]},
                              sensitivity="public", record_status="confirmed"),
            ]
            db.add_all(records)
            await db.flush()
            for r in records:
                reg("archive_records", r.id)
            counts["archive"] = len(records)

            # ===== ④ 接龙 1 个（10 人中 2 重复 + 3 未报名） =====
            signup = Signup(title="周六团建去不去", description="本周六下午校园烧烤团建", options=["去", "不去"], deadline=_now(2))
            db.add(signup)
            await db.flush()
            reg("signups", signup.id)
            names = ["张三", "李四", "王五", "赵六", "孙七", "周八", "吴九", "郑十", "林小夏", "陈一"]
            entries = [
                SignupEntry(signup_id=signup.id, name=name, option="去" if i % 3 else "不去",
                            source="text", is_duplicate=name in ("张三", "李四"))
                for i, name in enumerate(names)
            ]
            db.add_all(entries)
            await db.flush()
            for e in entries:
                reg("signup_entries", e.id)
            counts["signups"] = 1

            # 未报名（不在名单者）→ 催办待办（来源=signup）
            unsub = "王五、孙七、郑十"
            todo3 = TodoItem(content=f"催办接龙未报名名单：{unsub}", deadline=_now(2), status="pending")
            db.add(todo3)
            await db.flush()
            reg("todos", todo3.id)
            link3 = TodoLink(todo_id=todo3.id, source_type="signup", source_id=signup.id, label="接龙")
            db.add(link3)
            await db.flush()
            reg_objs([link3])
            counts["todos"] += 1

            # ===== ⑥ 生成物：简历 v1 预生成（含【待补充】行） =====
            artifact = Artifact(
                artifact_type="resume", title="林小夏·保研简历（v1）", direction="保研-计算机",
                content="教育背景：示例大学计算机科学与技术 2022 级\n科研经历：实验室科研助理，参与图像识别项目\n荣誉奖项：国家奖学金、ACM 银奖\n【待补充】实习经历细节",
                version=1, status="draft", source_ids={"archive": [r.id for r in records]},
            )
            db.add(artifact)
            await db.flush()
            reg("artifacts", artifact.id)

        # 事务提交后开启演示态
        _demo_enable()

    return {"ok": True, "seeded": counts, "demo_mode": True}


async def _delete_seeded_rows(db) -> None:
    """按 demo_seeds 登记回删（只删 seed 行）"""
    rows = (await db.execute(select(DemoSeed))).scalars().all()
    by_table: dict[str, list[int]] = {}
    for r in rows:
        by_table.setdefault(r.table_name, []).append(r.row_id)
    for table_name, model in _CLEAR_MODELS:
        ids = by_table.get(table_name)
        if ids:
            await db.execute(delete(model).where(model.id.in_(ids)))
    await db.execute(delete(DemoSeed))


async def clear_demo(db=None) -> None:
    """一键清空演示数据（只删登记行，不污染正式数据）；复位演示态"""
    if db is None:
        async with async_session_factory() as session:
            async with session.begin():
                await _delete_seeded_rows(session)
    else:
        await _delete_seeded_rows(db)
    _demo_disable()
