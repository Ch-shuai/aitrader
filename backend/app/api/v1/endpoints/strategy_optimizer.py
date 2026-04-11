"""
策略自优化 API - 基于历史数据自动优化策略参数
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.strategy_optimizer import get_strategy_optimizer
from app.core.logger import init_logging

router = APIRouter()


@router.post("/{strategy_id}/optimize")
async def optimize_strategy(
    strategy_id: int,
    start_date: str = Query(..., description="回测开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="回测结束日期 (YYYY-MM-DD)"),
    metric: str = Query("sharpe", description="优化指标: sharpe/return/win_rate/calmar"),
    max_combinations: int = Query(50, ge=10, le=200),
    db: Session = Depends(get_db)
):
    """
    优化策略参数

    通过网格搜索自动寻找最优参数组合
    """
    optimizer = get_strategy_optimizer(db)

    result = optimizer.optimize_strategy(
        strategy_id=strategy_id,
        start_date=start_date,
        end_date=end_date,
        metric=metric,
        max_combinations=max_combinations
    )

    return {
        "strategy_id": result.strategy_id,
        "best_params": result.best_params,
        "best_score": result.best_score,
        "optimization_time_seconds": result.optimization_time,
        "total_combinations_tested": len(result.all_results),
        "top_results": sorted(
            result.all_results,
            key=lambda x: x.get("score", 0),
            reverse=True
        )[:5]
    }


@router.post("/{strategy_id}/walk-forward")
async def walk_forward_optimization(
    strategy_id: int,
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
    train_period: int = Query(180, description="训练期天数"),
    test_period: int = Query(60, description="测试期天数"),
    metric: str = Query("sharpe", description="优化指标"),
    db: Session = Depends(get_db)
):
    """
    滚动前向优化

    使用滚动窗口验证策略参数的稳健性
    """
    optimizer = get_strategy_optimizer(db)

    result = optimizer.walk_forward_optimization(
        strategy_id=strategy_id,
        start_date=start_date,
        end_date=end_date,
        train_period=train_period,
        test_period=test_period,
        metric=metric
    )

    return result


@router.post("/auto-optimize-all")
async def auto_optimize_all_strategies(
    db: Session = Depends(get_db)
):
    """
    自动优化所有活跃策略

    对系统中所有活跃策略进行自动参数优化
    """
    optimizer = get_strategy_optimizer(db)
    results = optimizer.auto_optimize_all_strategies()

    return {
        "message": "自动优化完成",
        "optimized_count": len(results["optimized"]),
        "failed_count": len(results["failed"]),
        "details": results
    }


@router.post("/init-logs")
async def initialize_logging():
    """初始化日志系统"""
    init_logging()
    return {"message": "日志系统已初始化"}
