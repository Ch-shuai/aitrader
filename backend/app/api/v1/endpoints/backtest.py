"""
回测中心 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from app.core.database import get_db, BacktestResult, Strategy
from app.services.backtest_service import BacktestService

router = APIRouter()
backtest_service = BacktestService()


@router.post("/run")
async def run_backtest(
    strategy_id: int,
    start_date: str,
    end_date: str,
    initial_capital: float = 1000000.0,
    position_size: float = 0.2,
    stop_loss: float = 0.07,
    take_profit: float = 0.15,
    db: Session = Depends(get_db)
):
    """运行回测"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        return {"error": "策略不存在"}

    try:
        result = backtest_service.run_backtest(
            db=db,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        return {
            "backtest_id": result["id"],
            "strategy": strategy.name,
            "period": f"{start_date} to {end_date}",
            "summary": {
                "total_return": f"{result['total_return']:.2f}%",
                "annual_return": f"{result['annual_return']:.2f}%",
                "sharpe_ratio": f"{result['sharpe_ratio']:.2f}",
                "max_drawdown": f"{result['max_drawdown']:.2f}%",
                "win_rate": f"{result['win_rate']:.2f}%",
                "trade_count": result['trade_count'],
            },
            "status": "completed"
        }
    except Exception as e:
        return {"error": f"回测失败: {str(e)}"}


@router.get("/results")
async def list_backtest_results(
    strategy_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取回测结果列表"""
    query = db.query(BacktestResult)

    if strategy_id:
        query = query.filter(BacktestResult.strategy_id == strategy_id)

    results = query.order_by(BacktestResult.created_at.desc()).limit(limit).all()

    return {
        "total": len(results),
        "items": [
            {
                "id": r.id,
                "strategy_id": r.strategy_id,
                "start_date": r.start_date.strftime("%Y-%m-%d") if r.start_date else None,
                "end_date": r.end_date.strftime("%Y-%m-%d") if r.end_date else None,
                "initial_capital": r.initial_capital,
                "final_capital": r.final_capital,
                "total_return": f"{r.total_return:.2f}%" if r.total_return else None,
                "annual_return": f"{r.annual_return:.2f}%" if r.annual_return else None,
                "sharpe_ratio": round(r.sharpe_ratio, 2) if r.sharpe_ratio else None,
                "max_drawdown": f"{r.max_drawdown:.2f}%" if r.max_drawdown else None,
                "win_rate": f"{r.win_rate:.2f}%" if r.win_rate else None,
                "trade_count": r.trade_count,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
            }
            for r in results
        ]
    }


@router.get("/{backtest_id}")
async def get_backtest_detail(backtest_id: int, db: Session = Depends(get_db)):
    """获取回测详情"""
    result = db.query(BacktestResult).filter(BacktestResult.id == backtest_id).first()
    if not result:
        return {"error": "回测结果不存在"}

    strategy = db.query(Strategy).filter(Strategy.id == result.strategy_id).first()

    return {
        "id": result.id,
        "strategy": {
            "id": strategy.id if strategy else None,
            "name": strategy.name if strategy else "",
            "code": strategy.code if strategy else "",
        },
        "period": {
            "start": result.start_date.strftime("%Y-%m-%d") if result.start_date else None,
            "end": result.end_date.strftime("%Y-%m-%d") if result.end_date else None,
        },
        "capital": {
            "initial": result.initial_capital,
            "final": result.final_capital,
        },
        "returns": {
            "total": f"{result.total_return:.2f}%" if result.total_return else None,
            "annual": f"{result.annual_return:.2f}%" if result.annual_return else None,
        },
        "risk_metrics": {
            "sharpe_ratio": round(result.sharpe_ratio, 2) if result.sharpe_ratio else None,
            "max_drawdown": f"{result.max_drawdown:.2f}%" if result.max_drawdown else None,
            "volatility": result.params.get("volatility") if result.params else None,
        },
        "trade_stats": {
            "total_trades": result.trade_count,
            "win_rate": f"{result.win_rate:.2f}%" if result.win_rate else None,
        },
        "params": result.params,
        "created_at": result.created_at.strftime("%Y-%m-%d %H:%M:%S") if result.created_at else None,
    }


@router.get("/{backtest_id}/trades")
async def get_backtest_trades(backtest_id: int, db: Session = Depends(get_db)):
    """获取回测交易记录"""
    # 从params中获取交易记录
    result = db.query(BacktestResult).filter(BacktestResult.id == backtest_id).first()
    if not result:
        return {"error": "回测结果不存在"}

    trades = result.params.get("trades", []) if result.params else []

    return {
        "backtest_id": backtest_id,
        "total_trades": len(trades),
        "trades": trades
    }


@router.get("/{backtest_id}/equity-curve")
async def get_equity_curve(backtest_id: int, db: Session = Depends(get_db)):
    """获取权益曲线"""
    result = db.query(BacktestResult).filter(BacktestResult.id == backtest_id).first()
    if not result:
        return {"error": "回测结果不存在"}

    equity_curve = result.params.get("equity_curve", []) if result.params else []

    return {
        "backtest_id": backtest_id,
        "points": len(equity_curve),
        "data": equity_curve
    }


@router.post("/optimize/{strategy_id}")
async def optimize_strategy(
    strategy_id: int,
    start_date: str,
    end_date: str,
    param_grid: dict,
    metric: str = Query("sharpe", regex="^(sharpe|return|drawdown|win_rate)$"),
    db: Session = Depends(get_db)
):
    """策略参数优化"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        return {"error": "策略不存在"}

    try:
        optimization_result = backtest_service.optimize_parameters(
            db, strategy, start_date, end_date, param_grid, metric
        )

        return {
            "strategy_id": strategy_id,
            "optimization_metric": metric,
            "best_params": optimization_result["best_params"],
            "best_score": optimization_result["best_score"],
            "total_iterations": optimization_result["total_iterations"],
            "results": optimization_result["all_results"]
        }
    except Exception as e:
        return {"error": f"优化失败: {str(e)}"}


@router.delete("/{backtest_id}")
async def delete_backtest(backtest_id: int, db: Session = Depends(get_db)):
    """删除回测结果"""
    result = db.query(BacktestResult).filter(BacktestResult.id == backtest_id).first()
    if not result:
        return {"error": "回测结果不存在"}

    db.delete(result)
    db.commit()

    return {"message": "回测结果已删除"}
