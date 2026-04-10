"""
因子中心 API - 支持561个因子计算与管理
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from app.core.database import get_db, Stock, DailyPrice, FactorData
from app.services.factor_service import FactorService

router = APIRouter()
factor_service = FactorService()


@router.get("/categories")
async def get_factor_categories():
    """获取因子分类"""
    return {
        "categories": [
            {"id": "technical", "name": "技术因子", "count": 120, "description": "MA、MACD、RSI等技术指标"},
            {"id": "value", "name": "价值因子", "count": 85, "description": "PE、PB、股息率等估值指标"},
            {"id": "growth", "name": "成长因子", "count": 75, "description": "营收增长、利润增长等"},
            {"id": "quality", "name": "质量因子", "count": 90, "description": "ROE、ROA、盈利稳定性"},
            {"id": "momentum", "name": "动量因子", "count": 95, "description": "价格动量、收益动量"},
            {"id": "sentiment", "name": "情绪因子", "count": 56, "description": "舆情、资金流向、情绪指标"},
            {"id": "macro", "name": "宏观因子", "count": 40, "description": "利率、汇率、行业周期"},
        ]
    }


@router.get("/list")
async def get_factor_list(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取因子列表"""
    factors = factor_service.get_all_factors()

    if category:
        factors = [f for f in factors if f["category"] == category]

    if search:
        factors = [f for f in factors if search.lower() in f["name"].lower() or search.lower() in f["code"].lower()]

    return {
        "total": len(factors),
        "items": factors
    }


@router.post("/calculate/{code}")
async def calculate_factors(
    code: str,
    factor_codes: Optional[List[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """计算指定股票的因子"""
    stock = db.query(Stock).filter(Stock.code == code).first()
    if not stock:
        return {"error": "股票不存在"}

    try:
        count = factor_service.calculate_and_save_factors(
            db, code, factor_codes, start_date, end_date
        )
        return {
            "code": code,
            "message": f"因子计算完成，共{count}条记录",
            "calculated_count": count
        }
    except Exception as e:
        return {"error": f"因子计算失败: {str(e)}"}


@router.get("/{code}/values")
async def get_factor_values(
    code: str,
    factor_names: Optional[List[str]] = Query(None),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取股票因子值"""
    query = db.query(FactorData).filter(FactorData.code == code)

    if factor_names:
        query = query.filter(FactorData.factor_name.in_(factor_names))
    if start_date:
        query = query.filter(FactorData.date >= start_date)
    if end_date:
        query = query.filter(FactorData.date <= end_date)

    factors = query.order_by(FactorData.date.desc()).limit(limit).all()

    # 按日期分组
    result = {}
    for f in factors:
        date_str = f.date.strftime("%Y-%m-%d")
        if date_str not in result:
            result[date_str] = {"date": date_str, "factors": {}}
        result[date_str]["factors"][f.factor_name] = f.factor_value

    return {
        "code": code,
        "total_dates": len(result),
        "data": list(result.values())
    }


@router.get("/{code}/latest")
async def get_latest_factors(
    code: str,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取股票最新因子值"""
    stock = db.query(Stock).filter(Stock.code == code).first()
    if not stock:
        return {"error": "股票不存在"}

    # 获取最新日期
    latest = db.query(FactorData).filter(
        FactorData.code == code
    ).order_by(FactorData.date.desc()).first()

    if not latest:
        return {"error": "暂无因子数据"}

    query = db.query(FactorData).filter(
        FactorData.code == code,
        FactorData.date == latest.date
    )

    if category:
        query = query.filter(FactorData.factor_group == category)

    factors = query.all()

    return {
        "code": code,
        "date": latest.date.strftime("%Y-%m-%d"),
        "factors": {f.factor_name: f.factor_value for f in factors}
    }


@router.post("/batch-calculate")
async def batch_calculate_factors(
    codes: List[str],
    factor_category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """批量计算多只股票因子"""
    results = []
    for code in codes:
        try:
            count = factor_service.calculate_and_save_factors(
                db, code, category=factor_category
            )
            results.append({"code": code, "status": "success", "count": count})
        except Exception as e:
            results.append({"code": code, "status": "failed", "error": str(e)})

    success_count = len([r for r in results if r["status"] == "success"])
    return {
        "total": len(codes),
        "success": success_count,
        "failed": len(codes) - success_count,
        "results": results
    }


@router.get("/screening/rank")
async def factor_screening(
    factor_name: str,
    order: str = Query("desc", regex="^(asc|desc)$"),
    date: Optional[date] = None,
    industry: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """基于单因子股票筛选排序"""
    if not date:
        # 获取最新有数据的日期
        latest = db.query(FactorData).filter(
            FactorData.factor_name == factor_name
        ).order_by(FactorData.date.desc()).first()
        if latest:
            date = latest.date
        else:
            return {"error": "该因子暂无数据"}

    query = db.query(FactorData).filter(
        FactorData.factor_name == factor_name,
        FactorData.date == date
    )

    if order == "desc":
        query = query.order_by(FactorData.factor_value.desc())
    else:
        query = query.order_by(FactorData.factor_value.asc())

    results = query.limit(limit).all()

    # 获取股票基本信息
    items = []
    for r in results:
        stock = db.query(Stock).filter(Stock.code == r.code).first()
        items.append({
            "code": r.code,
            "name": stock.name if stock else "",
            "industry": stock.industry if stock else "",
            "factor_value": r.factor_value,
            "date": r.date.strftime("%Y-%m-%d")
        })

    if industry:
        items = [item for item in items if item["industry"] == industry]

    return {
        "factor": factor_name,
        "date": date.strftime("%Y-%m-%d"),
        "total": len(items),
        "items": items
    }


@router.get("/correlation/analysis")
async def factor_correlation(
    code: str,
    factor_names: List[str] = Query(...),
    days: int = Query(252, ge=60, le=1000),
    db: Session = Depends(get_db)
):
    """因子相关性分析"""
    return factor_service.calculate_correlation(db, code, factor_names, days)


@router.get("/ic-analysis/{factor_name}")
async def factor_ic_analysis(
    factor_name: str,
    days: int = Query(60, ge=20, le=252),
    db: Session = Depends(get_db)
):
    """因子IC分析(信息系数)"""
    return factor_service.calculate_ic(db, factor_name, days)
