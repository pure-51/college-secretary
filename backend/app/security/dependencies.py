"""FastAPI 安全依赖（ADR 000 §6：loopback 正则 CORS + X-Local-Token + 写接口限流）"""
import time
from collections import defaultdict

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

TOKEN_EXEMPT_PATHS = {"/api/health", "/api/config", "/api/admin/demo-status", "/api/admin/seed"}


class LocalTokenMiddleware(BaseHTTPMiddleware):
    """X-Local-Token 校验。ENABLE_TOKEN 默认 False（S0 过渡），S1 前置 True。"""

    async def dispatch(self, request: Request, call_next):
        if settings.ENABLE_TOKEN and request.url.path not in TOKEN_EXEMPT_PATHS:
            token = request.headers.get("X-Local-Token")
            if token != settings.LOCAL_TOKEN:
                return JSONResponse(status_code=401, content={"detail": "无效的本地令牌"})
        return await call_next(request)


_requests: dict[tuple[str, str], list[float]] = defaultdict(list)


def rate_limit(prefix: str):
    """写接口限流：同 IP+路由前缀 滑动窗口，每分钟上限 RATE_LIMIT_PER_MIN。"""
    limit = settings.RATE_LIMIT_PER_MIN

    def _dep(request: Request):
        key = (request.client.host if request.client else "local", prefix)
        now = time.time()
        window = [t for t in _requests[key] if now - t < 60]
        if len(window) >= limit:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
        window.append(now)
        _requests[key] = window

    return _dep
