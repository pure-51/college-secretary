"""FastAPI 主应用"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.config import settings
from app.security.dependencies import LocalTokenMiddleware
from app.routers import inbox, documents, schedule, ai_report, ai_consult, ocr, files, export as export_router, admin, career, papers, affairs, orchestrate, tasks

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="大学生秘书智能助手 API",
    description="AI-powered college secretary backend",
    version="1.0.0",
    lifespan=lifespan,
)

# 安全加固（ADR 000 §6）：CORS 收紧为 loopback 任意端口正则，allow_credentials=False；
# X-Local-Token 中间件（ENABLE_TOKEN 默认 False 渐进启用，S1 前置 True）
app.add_middleware(LocalTokenMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_LOOPBACK_ALLOW_REGEX,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/api/config")
async def get_config():
    return {
        "llm_model": settings.LLM_MODEL,
        "llm_base_url": settings.LLM_BASE_URL,
        "ocr_enabled": settings.OCR_ENABLED,
        "local_token": settings.LOCAL_TOKEN,  # 前端唯一 token 来源（ADR 000 §6，S1 前置）
    }

# 注册路由
app.include_router(inbox.router, prefix="/api/inbox", tags=["收件箱"])
app.include_router(documents.router, prefix="/api/knowledge", tags=["知识库"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["日程"])
app.include_router(ai_report.router, prefix="/api/ai", tags=["AI 汇报"])
app.include_router(ai_consult.router, prefix="/api/ai", tags=["AI 咨询"])
app.include_router(ocr.router, prefix="/api", tags=["OCR"])
app.include_router(files.router, tags=["文件"])
app.include_router(export_router.router, tags=["导出"])
app.include_router(admin.router, tags=["管理"])
app.include_router(career.router, tags=["生涯档案官"])
app.include_router(papers.router, tags=["科研论文库"])
app.include_router(affairs.router, tags=["班务助理"])
app.include_router(orchestrate.router, tags=["AI 路由"])
app.include_router(tasks.router, tags=["长任务"])
