"""
A股智能研究与交易平台 - 主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db
from app.api.v1.router import api_router
from app.tasks.scheduler import start_scheduler, stop_scheduler
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    print("🚀 启动 A股智能研究与交易平台...")
    init_db()
    start_scheduler()
    print("✅ 系统初始化完成")
    yield
    # 关闭
    print("👋 正在关闭系统...")
    stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A股智能研究与交易平台 - 支持多策略、多因子、回测调优、学习蒸馏",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api": settings.API_V1_STR
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
