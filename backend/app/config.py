"""应用配置管理"""
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
TOKEN_FILE = DATA_DIR / "local_token.txt"


def _resolve_local_token() -> str:
    """LOCAL_TOKEN 解析：显式配置优先；否则首启自动生成并持久化（ADR 000 §6，S1 前置）。"""
    explicit = os.getenv("LOCAL_TOKEN", "").strip()
    if explicit:
        return explicit
    if TOKEN_FILE.exists():
        saved = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if saved:
            return saved
    token = secrets.token_urlsafe(32)
    try:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(token, encoding="utf-8")
    except OSError:
        pass  # 磁盘不可写时退回内存 token（仅本会话有效）
    return token


class Settings:
    # 数据库
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATA_DIR}/database/college_secretary.db")

    # LLM API
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")

    # 服务器
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8002"))

    # 文件存储
    UPLOAD_DIR: Path = DATA_DIR / "uploads"

    # OCR
    OCR_ENABLED: bool = os.getenv("OCR_ENABLED", "true").lower() == "true"

    # 安全（P-4）—— 见 ADR 000 §6。S1 起 ENABLE_TOKEN 默认 True。
    LOCAL_TOKEN: str = _resolve_local_token()
    ENABLE_TOKEN: bool = os.getenv("ENABLE_TOKEN", "true").lower() == "true"  # S1 前置 True（ADR §7 裁决）
    CORS_ORIGINS: list = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
    CORS_LOOPBACK_ALLOW_REGEX: str = os.getenv(
        "CORS_LOOPBACK_ALLOW_REGEX", r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    )
    RATE_LIMIT_PER_MIN: int = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))
    SENSITIVE_FIELDS: list = [
        f.strip() for f in os.getenv("SENSITIVE_FIELDS", "score,amount,id_card,phone,gpa,rank").split(",") if f.strip()
    ]

    # LLM 调用（P-1）—— ADR 000 §6：超时统一 120s，重试 3 次
    LLM_TIMEOUT_SECONDS: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
    LLM_CACHE_TTL: int = int(os.getenv("LLM_CACHE_TTL", "600"))

    # 演示模式（P-5）
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"

    # 导出（P-3）
    EXPORT_DIR: Path = DATA_DIR / "exports"

    # 文件上传
    ALLOWED_EXTENSIONS: list = [".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg", ".xlsx", ".csv"]

settings = Settings()

# 确保目录存在
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "database").mkdir(parents=True, exist_ok=True)
