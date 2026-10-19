"""技能构建辅助（ADR 000 §1）"""
from typing import Optional, Type

from pydantic import BaseModel

from app.services.skill_registry import Skill
from app.services.prompts import load_prompt


def build_skill(
    name: str,
    output_schema: Optional[Type[BaseModel]] = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
    cache_ttl: int = 600,
    retry: int = 3,
    json_mode: bool = True,
    version: str = "v1",
) -> Skill:
    prompts = load_prompt(name, version)
    return Skill(
        name=name,
        system_prompt=prompts["system"],
        user_template=prompts["user"],
        output_schema=output_schema,
        temperature=temperature,
        max_tokens=max_tokens,
        cache_ttl=cache_ttl,
        retry=retry,
        json_mode=json_mode,
        version=version,
    )
