"""LLM 结果缓存（TTL 内存缓存，ADR 000 §1）
缓存 key 含 skill 名 + prompt version + payload 哈希，杜绝改 prompt 命中旧缓存。
"""
import time
import json
import hashlib
from typing import Any, Optional

class TTLCache:
    def __init__(self, ttl: int = 600):
        self._ttl = ttl
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._data.get(key)
        if item is None:
            return None
        ts, value = item
        if time.time() - ts > self._ttl:
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._data[key] = (time.time(), value)

    def clear(self) -> None:
        self._data.clear()

    @staticmethod
    def make_key(parts: list) -> str:
        raw = json.dumps(parts, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
