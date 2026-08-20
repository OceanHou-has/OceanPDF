from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.core.config import settings
from app.api import upload, translate, task, pdf, annotation, export, document_parser

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO"
)

# 创建FastAPI应用
app = FastAPI(
    title="OceanPDF Backend API",
    description="桌面端PDF论文翻译软件 - 主后端服务",
    version="2.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(translate.router, prefix="/api/v1", tags=["translate"])
app.include_router(task.router, prefix="/api/v1", tags=["task"])
app.include_router(pdf.router, prefix="/api/v1", tags=["pdf"])
app.include_router(annotation.router, prefix="/api/v1", tags=["annotation"])
app.include_router(export.router, prefix="/api/v1", tags=["export"])
app.include_router(document_parser.router, prefix="/api/v1", tags=["document_parser"])

@app.get("/")
async def root():
    """根路径"""
    return {
        "code": 200,
        "message": "OceanPDF Backend API",
        "data": {
            "version": "2.0.0",
            "status": "running"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "code": 200,
        "message": "success",
        "data": {"status": "healthy"}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
