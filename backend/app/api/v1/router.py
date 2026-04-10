"""
API路由聚合
"""
from fastapi import APIRouter
from app.api.v1.endpoints import stocks, factors, strategies, signals, backtest, news, ai, scheduler, sync

api_router = APIRouter()

# 股票相关
api_router.include_router(stocks.router, prefix="/stocks", tags=["股票数据"])

# 因子相关
api_router.include_router(factors.router, prefix="/factors", tags=["因子中心"])

# 策略相关
api_router.include_router(strategies.router, prefix="/strategies", tags=["策略中心"])

# 信号相关
api_router.include_router(signals.router, prefix="/signals", tags=["交易信号"])

# 回测相关
api_router.include_router(backtest.router, prefix="/backtest", tags=["回测中心"])

# 资讯相关
api_router.include_router(news.router, prefix="/news", tags=["资讯中心"])

# AI相关
api_router.include_router(ai.router, prefix="/ai", tags=["AI服务"])

# 定时任务相关
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["定时任务"])

# 数据同步相关
api_router.include_router(sync.router, prefix="/sync", tags=["数据同步"])
