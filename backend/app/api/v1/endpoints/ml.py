"""
机器学习 API - 预测模型训练和预测
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.services.ml_service import ml_service

router = APIRouter()


@router.post("/train/{code}")
async def train_model(
    code: str,
    model_type: str = Query("xgboost", regex="^(xgboost|lightgbm)$"),
    db: Session = Depends(get_db)
):
    """训练单只股票预测模型"""
    result = ml_service.train_model(db, code, model_type)
    return result


@router.post("/batch-train")
async def batch_train_models(
    max_stocks: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """批量训练多只股票模型"""
    result = ml_service.batch_train(db, max_stocks)
    return result


@router.get("/predict/{code}")
async def predict_stock(
    code: str,
    days_ahead: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """预测股票未来走势"""
    result = ml_service.predict(db, code, days_ahead)
    return result


@router.get("/performance")
async def get_model_performance(code: Optional[str] = None):
    """获取模型性能报告"""
    return ml_service.get_model_performance(code)


@router.get("/status")
async def get_ml_status():
    """获取ML服务状态"""
    from app.services.ml_service import ML_AVAILABLE
    return {
        "ml_available": ML_AVAILABLE,
        "supported_models": ["xgboost", "lightgbm"] if ML_AVAILABLE else [],
        "trained_models": len(ml_service.models)
    }
