"""LLM 调用底层客户端（ADR 000 §6：超时统一 120s，重试 3 次指数退避）"""
import asyncio
import httpx
from app.config import settings

class AsyncLLMClient:
    def __init__(self, api_key=None, base_url=None, model=None, timeout=None, max_retries=None):
        self.api_key = api_key if api_key is not None else settings.LLM_API_KEY
        self.base_url = base_url if base_url is not None else settings.LLM_BASE_URL
        self.model = model if model is not None else settings.LLM_MODEL
        self.timeout = timeout if timeout is not None else settings.LLM_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else settings.LLM_MAX_RETRIES

    async def call(
        self,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        json_mode: bool = False,
        retry: int | None = None,
    ) -> str:
        """调用 LLM，失败返回可解析占位文本（不抛异常）"""
        retry = retry if retry is not None else self.max_retries
        if not self.api_key:
            return '{"error": "LLM API Key 未配置"}' if json_mode else ""

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        url = f"{self.base_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        for attempt in range(retry):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, headers=headers, json=body)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
            except (httpx.TimeoutException, httpx.HTTPError, KeyError, ValueError):
                pass
            if attempt < retry - 1:
                await asyncio.sleep(2 ** attempt)  # 1s / 2s / 4s
        return '{"error": "LLM 调用失败"}' if json_mode else ""
