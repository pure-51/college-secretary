"""技能包导出与装配（ADR 000 §1：模块加载即注册到全局 registry）"""
from app.services.skill_registry import registry
from app.services.skills import inbox, summary, career, papers, affairs, orchestrate, legacy

SKILL_MODULES = [inbox, summary, career, papers, affairs, orchestrate, legacy]


def register_all() -> None:
    for mod in SKILL_MODULES:
        for skill in getattr(mod, "SKILLS", []):
            registry.register(skill)


register_all()
