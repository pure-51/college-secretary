"""技能注册表核心（ADR 000 §1：唯一 LLM 底座 run(task, payload)）
流程：pre_hooks → 缓存查询 → llm_client.call → schema 校验 → 缓存写入。
"""
import re
import json
from dataclasses import dataclass, field
from typing import Any, Optional, Type
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.services.llm_client import AsyncLLMClient
from app.services.cache_service import TTLCache


class SkillNotFoundError(Exception):
    """未知技能，路由层转 400"""


@dataclass
class Skill:
    name: str
    system_prompt: str = ""
    user_template: str = ""
    output_schema: Optional[Type[BaseModel]] = None  # None = 纯文本输出
    temperature: float = 0.1
    max_tokens: int = 2048
    cache_ttl: int = 600
    retry: int = 3
    json_mode: bool = True
    version: str = "v1"
    pre_hooks: list = field(default_factory=list)  # S0-3 挂 consent/redaction/demo


class SkillRegistry:
    def __init__(self, llm_client: AsyncLLMClient, cache: TTLCache):
        self.llm_client = llm_client
        self.cache = cache
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self) -> list[str]:
        return sorted(self._skills.keys())

    def cache_key(self, skill: Skill, payload: dict) -> str:
        return self.cache.make_key([skill.name, skill.version, payload])

    def render_user(self, skill: Skill, payload: dict) -> str:
        text = skill.user_template
        for key, value in payload.items():
            text = text.replace("{{" + key + "}}", str(value))
        return re.sub(r"\{\{[^}]*\}\}", "", text)  # 清理残留占位符

    async def run(self, task: str, payload: dict) -> Any:
        skill = self._skills.get(task)
        if skill is None:
            raise SkillNotFoundError(f"未知技能: {task}")

        for hook in skill.pre_hooks:
            payload = hook(payload, skill=skill)

        cache_key = self.cache_key(skill, payload)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        messages = [
            {"role": "system", "content": skill.system_prompt},
            {"role": "user", "content": self.render_user(skill, payload)},
        ]
        text = await self.llm_client.call(
            messages=messages,
            temperature=skill.temperature,
            max_tokens=skill.max_tokens,
            json_mode=skill.json_mode,
            retry=skill.retry,
        )
        result = self._parse(text, skill)
        self.cache.set(cache_key, result, ttl=skill.cache_ttl)
        return result

    def _parse(self, text: str, skill: Skill) -> Any:
        if skill.output_schema is None:
            return text.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]
        try:
            data = json.loads(text)
            return skill.output_schema.model_validate(data)
        except (json.JSONDecodeError, ValidationError):
            return skill.output_schema()


# 模块级单例（测试时替换 .llm_client 为 MockLLM 即可注入）
registry = SkillRegistry(
    llm_client=AsyncLLMClient(),
    cache=TTLCache(ttl=settings.LLM_CACHE_TTL),
)
