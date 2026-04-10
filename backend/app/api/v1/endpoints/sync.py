"""
数据同步 API
"""
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.sync_service import sync_service

router = APIRouter()


@router.post("/initialize")
async def initialize_data(background_tasks: BackgroundTasks):
    """
    初始化数据 (首次运行)

    在后台执行完整的数据初始化:
    1. 同步股票列表
    2. 同步历史行情
    3. 计算因子
    4. 同步新闻
    """
    def progress_callback(step_name: str, current: int, total: int):
        print(f"[初始化进度] {step_name}: {current}/{total}")

    # 在后台运行初始化
    background_tasks.add_task(sync_service.initialize_data, progress_callback)

    return {
        "message": "数据初始化任务已启动",
        "status": "running",
        "note": "这是一个耗时操作，将在后台执行"
    }


@router.post("/daily-update")
async def daily_update(background_tasks: BackgroundTasks):
    """
    执行每日增量更新

    更新内容:
    1. 新增股票列表
    2. 最新日线行情
    3. 增量计算因子
    4. 最新新闻
    """
    background_tasks.add_task(sync_service.daily_update)

    return {
        "message": "每日更新任务已启动",
        "status": "running"
    }


@router.get("/status")
async def get_sync_status():
    """获取数据同步状态"""
    return sync_service.get_sync_status()


@router.post("/stocks")
async def sync_stock_list():
    """手动触发股票列表同步"""
    from app.services.data_service import StockDataService
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        service = StockDataService()
        count = service.sync_stock_list(db)
        return {
            "message": f"股票列表同步完成",
            "new_stocks": count
        }
    finally:
        db.close()


@router.post("/prices")
async def sync_prices(code: Optional[str] = None):
    """手动触发行情数据同步"""
    from app.services.data_service import StockDataService
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        service = StockDataService()
        count = service.sync_daily_prices(db, code)
        return {
            "message": f"行情数据同步完成",
            "new_records": count
        }
    finally:
        db.close()


@router.post("/factors")
async def calculate_factors(code: Optional[str] = None):
    """手动触发因子计算"""
    from app.services.factor_service import FactorService
    from app.core.database import SessionLocal, Stock

    db = SessionLocal()
    try:
        service = FactorService()

        if code:
            count = service.calculate_and_save_factors(db, code)
            return {
                "message": f"因子计算完成",
                "code": code,
                "new_factors": count
            }
        else:
            # 批量计算
            result = service.batch_calculate_all_factors(db)
            return {
                "message": "批量因子计算完成",
                "result": result
            }
    finally:
        db.close()
