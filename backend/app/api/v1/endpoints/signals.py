"""
交易信号 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from app.core.database import get_db, Signal, Strategy, Stock

router = APIRouter()


@router.get("/list")
async def list_signals(
    code: Optional[str] = None,
    strategy_id: Optional[int] = None,
    signal_type: Optional[str] = None,
    status: Optional[str] = None,
    min_confidence: Optional[float] = None,
    min_buy_grade: Optional[int] = Query(None, ge=1, le=5),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """获取交易信号列表"""
    query = db.query(Signal)

    if code:
        query = query.filter(Signal.code == code)
    if strategy_id:
        query = query.filter(Signal.strategy_id == strategy_id)
    if signal_type:
        query = query.filter(Signal.signal_type == signal_type)
    if status:
        query = query.filter(Signal.status == status)
    if min_confidence:
        query = query.filter(Signal.confidence >= min_confidence)
    if min_buy_grade:
        query = query.filter(Signal.buy_grade >= min_buy_grade)
    if start_date:
        query = query.filter(Signal.created_at >= start_date)
    if end_date:
        query = query.filter(Signal.created_at <= end_date)

    signals = query.order_by(Signal.created_at.desc()).limit(limit).all()

    result = []
    for s in signals:
        stock = db.query(Stock).filter(Stock.code == s.code).first()
        strategy = db.query(Strategy).filter(Strategy.id == s.strategy_id).first() if s.strategy_id else None

        result.append({
            "id": s.id,
            "code": s.code,
            "name": stock.name if stock else "",
            "strategy_id": s.strategy_id,
            "strategy_name": strategy.name if strategy else "",
            "signal_type": s.signal_type,
            "trigger_price": s.trigger_price,
            "confidence": s.confidence,
            "reason": s.reason,
            "buy_grade": s.buy_grade,
            "status": s.status,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else None,
        })

    return {
        "total": len(result),
        "items": result
    }


@router.get("/today")
async def get_today_signals(
    min_buy_grade: int = Query(3, ge=1, le=5),
    db: Session = Depends(get_db)
):
    """获取今日信号"""
    today = datetime.now().date()

    signals = db.query(Signal).filter(
        Signal.created_at >= today,
        Signal.buy_grade >= min_buy_grade,
        Signal.status == "pending"
    ).order_by(Signal.confidence.desc()).all()

    result = []
    for s in signals:
        stock = db.query(Stock).filter(Stock.code == s.code).first()
        result.append({
            "id": s.id,
            "code": s.code,
            "name": stock.name if stock else "",
            "signal_type": s.signal_type,
            "trigger_price": s.trigger_price,
            "confidence": s.confidence,
            "reason": s.reason,
            "buy_grade": s.buy_grade,
        })

    return {
        "date": today.strftime("%Y-%m-%d"),
        "total": len(result),
        "buy_signals": len([s for s in result if s["signal_type"] == "buy"]),
        "sell_signals": len([s for s in result if s["signal_type"] == "sell"]),
        "items": result
    }


@router.get("/high-grade")
async def get_high_grade_signals(
    min_grade: int = Query(4, ge=4, le=5),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取高等级买点信号 (4-5级)"""
    signals = db.query(Signal).filter(
        Signal.buy_grade >= min_grade,
        Signal.signal_type == "buy",
        Signal.status == "pending"
    ).order_by(Signal.created_at.desc()).limit(limit).all()

    result = []
    for s in signals:
        stock = db.query(Stock).filter(Stock.code == s.code).first()
        result.append({
            "id": s.id,
            "code": s.code,
            "name": stock.name if stock else "",
            "industry": stock.industry if stock else "",
            "trigger_price": s.trigger_price,
            "confidence": s.confidence,
            "buy_grade": s.buy_grade,
            "reason": s.reason,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else None,
        })

    return {
        "grade_level": f"{min_grade}-5级",
        "total": len(result),
        "items": result
    }


@router.get("/{signal_id}")
async def get_signal_detail(signal_id: int, db: Session = Depends(get_db)):
    """获取信号详情"""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        return {"error": "信号不存在"}

    stock = db.query(Stock).filter(Stock.code == signal.code).first()
    strategy = db.query(Strategy).filter(Strategy.id == signal.strategy_id).first() if signal.strategy_id else None

    return {
        "id": signal.id,
        "code": signal.code,
        "name": stock.name if stock else "",
        "industry": stock.industry if stock else "",
        "strategy": {
            "id": strategy.id if strategy else None,
            "name": strategy.name if strategy else "",
            "type": strategy.strategy_type if strategy else "",
        },
        "signal_type": signal.signal_type,
        "trigger_price": signal.trigger_price,
        "confidence": signal.confidence,
        "reason": signal.reason,
        "buy_grade": signal.buy_grade,
        "status": signal.status,
        "created_at": signal.created_at.strftime("%Y-%m-%d %H:%M:%S") if signal.created_at else None,
    }


@router.post("/{signal_id}/confirm")
async def confirm_signal(signal_id: int, db: Session = Depends(get_db)):
    """确认信号"""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        return {"error": "信号不存在"}

    signal.status = "confirmed"
    db.commit()

    return {"message": "信号已确认", "signal_id": signal_id}


@router.post("/{signal_id}/execute")
async def execute_signal(signal_id: int, db: Session = Depends(get_db)):
    """执行信号"""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        return {"error": "信号不存在"}

    signal.status = "executed"
    db.commit()

    return {"message": "信号已执行", "signal_id": signal_id}


@router.post("/{signal_id}/cancel")
async def cancel_signal(signal_id: int, reason: str = "", db: Session = Depends(get_db)):
    """取消信号"""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        return {"error": "信号不存在"}

    signal.status = "cancelled"
    db.commit()

    return {"message": "信号已取消", "signal_id": signal_id, "reason": reason}


@router.get("/stats/daily")
async def get_daily_signal_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """获取信号统计"""
    from sqlalchemy import func

    # 按日期统计
    stats = db.query(
        func.date(Signal.created_at).label('date'),
        func.count(Signal.id).label('count'),
        func.avg(Signal.confidence).label('avg_confidence'),
        func.avg(Signal.buy_grade).label('avg_grade')
    ).filter(
        Signal.created_at >= datetime.now() - __import__('datetime').timedelta(days=days)
    ).group_by(
        func.date(Signal.created_at)
    ).order_by(func.date(Signal.created_at).desc()).all()

    return {
        "days": days,
        "stats": [
            {
                "date": s.date.strftime("%Y-%m-%d"),
                "total_signals": s.count,
                "avg_confidence": round(s.avg_confidence, 2) if s.avg_confidence else 0,
                "avg_grade": round(s.avg_grade, 2) if s.avg_grade else 0,
            }
            for s in stats
        ]
    }


@router.post("/clear-expired")
async def clear_expired_signals(days: int = Query(30, ge=1, le=90), db: Session = Depends(get_db)):
    """清理过期信号"""
    cutoff_date = datetime.now() - __import__('datetime').timedelta(days=days)

    expired = db.query(Signal).filter(
        Signal.created_at < cutoff_date,
        Signal.status == "pending"
    ).all()

    count = 0
    for s in expired:
        s.status = "expired"
        count += 1

    db.commit()

    return {"message": f"已清理{count}条过期信号"}
