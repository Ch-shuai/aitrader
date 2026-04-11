"""
日志系统 API - 查询和管理系统日志
"""
from fastapi import APIRouter, Query
from typing import Optional
from app.core.logger import LogReader, init_logging

router = APIRouter()


@router.get("/operations")
async def get_operation_logs(
    limit: int = Query(100, ge=1, le=1000),
    hours: Optional[int] = Query(None, ge=1, le=720)
):
    """获取操作日志"""
    if hours:
        logs = LogReader.get_recent_operations(hours)
    else:
        logs = LogReader.read_logs("operation", limit)
    return {"logs": logs, "count": len(logs)}


@router.get("/errors")
async def get_error_logs(
    limit: int = Query(100, ge=1, le=1000)
):
    """获取错误日志"""
    logs = LogReader.read_logs("error", limit)
    return {"logs": logs, "count": len(logs)}


@router.get("/backtest")
async def get_backtest_logs(
    limit: int = Query(100, ge=1, le=1000)
):
    """获取回测日志"""
    logs = LogReader.read_logs("backtest", limit)
    return {"logs": logs, "count": len(logs)}


@router.get("/strategy")
async def get_strategy_logs(
    limit: int = Query(100, ge=1, le=1000)
):
    """获取策略日志"""
    logs = LogReader.read_logs("strategy", limit)
    return {"logs": logs, "count": len(logs)}


@router.get("/stats")
async def get_system_stats():
    """获取系统统计信息"""
    stats = LogReader.get_system_stats()
    return stats


@router.post("/init")
async def init_logs():
    """初始化日志系统"""
    init_logging()
    return {"message": "日志系统已初始化"}
