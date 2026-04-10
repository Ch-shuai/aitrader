"""
市场结构 API - 市场环境、板块轮动、情绪监控
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.market_service import market_service

router = APIRouter()


@router.get("/environment")
async def get_market_environment(db: Session = Depends(get_db)):
    """获取当前市场环境评估"""
    return market_service.analyze_market_environment(db)


@router.get("/sectors")
async def get_sector_rotation(
    days: int = Query(20, ge=5, le=60),
    db: Session = Depends(get_db)
):
    """获取板块轮动情况"""
    return market_service.get_sector_rotation(db, days)


@router.get("/sentiment")
async def get_market_sentiment(db: Session = Depends(get_db)):
    """获取综合市场情绪"""
    return market_service.get_market_sentiment(db)


@router.get("/risk-warning/{code}")
async def get_risk_warning(code: str, db: Session = Depends(get_db)):
    """获取个股风险预警"""
    return market_service.get_risk_warning(db, code)


@router.get("/overview")
async def get_market_overview(db: Session = Depends(get_db)):
    """获取市场全景概览"""
    environment = market_service.analyze_market_environment(db)
    sectors = market_service.get_sector_rotation(db, days=20)
    sentiment = market_service.get_market_sentiment(db)

    return {
        "date": environment.get("date"),
        "environment": environment.get("environment"),
        "sentiment": sentiment.get("interpretation"),
        "sentiment_index": sentiment.get("composite_index"),
        "hot_sectors": sectors.get("hot_sectors", [])[:3],
        "position_advice": environment.get("recommendation")
    }
