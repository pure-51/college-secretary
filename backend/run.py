"""启动脚本"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=8002,
        reload=True,
        log_level="info",
    )
