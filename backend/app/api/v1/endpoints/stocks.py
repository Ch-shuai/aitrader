"""
股票数据API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db, Stock, DailyPrice
from app.services.data_service import StockDataService

router = APIRouter()
stock_service = StockDataService()


@router.get("/")
async def get_stocks(
    industry: Optional[str] = None,
    market: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取股票列表"""
    query = db.query(Stock)
    if industry:
        query = query.filter(Stock.industry == industry)
    if market:
        query = query.filter(Stock.market == market)

    stocks = query.all()
    return {
        "total": len(stocks),
        "items": [
            {
                "code": s.code,
                "name": s.name,
                "industry": s.industry,
                "market": s.market,
            }
            for s in stocks
        ]
    }


@router.get("/{code}")
async def get_stock_detail(code: str, db: Session = Depends(get_db)):
    """获取股票详情"""
    stock = db.query(Stock).filter(Stock.code == code).first()
    if not stock:
        return {"error": "股票不存在"}

    # 获取最新行情
    latest_price = db.query(DailyPrice).filter(
        DailyPrice.code == code
    ).order_by(DailyPrice.date.desc()).first()

    return {
        "code": stock.code,
        "name": stock.name,
        "industry": stock.industry,
        "market": stock.market,
        "latest_price": {
            "close": latest_price.close if latest_price else None,
            "change": latest_price.pct_change if latest_price else None,
            "date": latest_price.date.strftime("%Y-%m-%d") if latest_price else None,
        } if latest_price else None
    }


@router.get("/{code}/prices")
async def get_stock_prices(
    code: str,
    days: int = Query(252, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取股票历史行情"""
    df = stock_service.get_stock_data(db, code, days)

    if df.empty:
        return {"error": "无数据"}

    return {
        "code": code,
        "days": len(df),
        "data": df.to_dict(orient="records")
    }


@router.post("/sync/list")
async def sync_stock_list(db: Session = Depends(get_db)):
    """同步股票列表"""
    count = stock_service.sync_stock_list(db)
    return {"message": f"同步完成，新增{count}只股票"}


@router.post("/sync/prices")
async def sync_prices(code: Optional[str] = None, db: Session = Depends(get_db)):
    """同步行情数据"""
    count = stock_service.sync_daily_prices(db, code)
    return {"message": f"同步完成，新增{count}条记录"}
