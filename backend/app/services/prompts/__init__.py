"""版本化 prompt 索引（ADR 000 §1）
目录结构：services/prompts/<domain>/<task>/<version>/system.txt + user.txt
模板占位符 {{var}}，渲染时由 SkillRegistry.render_user 替换。
"""
from pathlib import Path

PROMPT_ROOT = Path(__file__).parent

def _read_prompt(skill_name: str, version: str, kind: str) -> str:
    domain, task = skill_name.split(".", 1)
    path = PROMPT_ROOT / domain / task / version / f"{kind}.txt"
    return path.read_text(encoding="utf-8") if path.exists() else ""

def load_prompt(skill_name: str, version: str = "v1") -> dict:
    return {
        "system": _read_prompt(skill_name, version, "system"),
        "user": _read_prompt(skill_name, version, "user"),
    }
