"""
本地数据导入 API - 从本地目录加载股票历史数据
"""
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.services.local_data_service import local_data_service

router = APIRouter()


@router.get("/summary")
async def get_local_data_summary():
    """获取本地数据概览"""
    return local_data_service.get_data_summary()


@router.get("/stocks")
async def discover_local_stocks():
    """发现本地数据目录中的所有股票"""
    stocks = local_data_service.discover_stocks()
    return {
        "total": len(stocks),
        "stocks": stocks
    }


@router.post("/import/{code}")
async def import_single_stock(code: str, db: Session = Depends(get_db)):
    """导入单只股票数据"""
    count = local_data_service.import_stock_to_db(db, code)
    return {
        "code": code,
        "imported_records": count,
        "message": f"成功导入 {count} 条记录"
    }


@router.post("/import-all")
async def import_all_stocks(
    background_tasks: BackgroundTasks,
    limit: Optional[int] = Query(None, description="限制导入股票数量"),
    db: Session = Depends(get_db)
):
    """批量导入所有本地股票数据"""
    # 在后台运行导入任务
    background_tasks.add_task(local_data_service.batch_import, db, limit)

    return {
        "message": "批量导入任务已启动",
        "status": "running",
        "note": "这是一个耗时操作，将在后台执行"
    }


@router.get("/preview/{code}")
async def preview_stock_data(code: str, rows: int = Query(10, ge=1, le=100)):
    """预览股票数据"""
    df = local_data_service.read_stock_data(code)

    if df is None:
        return {"error": "无法读取数据"}

    preview_data = df.tail(rows).to_dict('records')

    # 转换日期格式
    for row in preview_data:
        if 'date' in row and hasattr(row['date'], 'strftime'):
            row['date'] = row['date'].strftime("%Y-%m-%d")

    return {
        "code": code,
        "total_rows": len(df),
        "columns": list(df.columns),
        "date_range": {
            "start": df['date'].min().strftime("%Y-%m-%d") if len(df) > 0 else None,
            "end": df['date'].max().strftime("%Y-%m-%d") if len(df) > 0 else None,
        },
        "preview": preview_data
    }
