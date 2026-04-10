"""
定时任务管理 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.services.scheduler_service import scheduler_service

router = APIRouter()


@router.get("/jobs")
async def get_scheduler_jobs():
    """获取所有定时任务"""
    jobs = scheduler_service.get_jobs()
    return {
        "status": "running" if scheduler_service.scheduler.running else "stopped",
        "jobs": jobs
    }


@router.post("/start")
async def start_scheduler():
    """启动定时任务调度器"""
    try:
        scheduler_service.start()
        return {"message": "定时任务调度器已启动"}
    except Exception as e:
        return {"error": f"启动失败: {str(e)}"}


@router.post("/stop")
async def stop_scheduler():
    """停止定时任务调度器"""
    try:
        scheduler_service.shutdown()
        return {"message": "定时任务调度器已停止"}
    except Exception as e:
        return {"error": f"停止失败: {str(e)}"}


@router.post("/run/{job_id}")
async def run_job_now(job_id: str):
    """立即执行某个定时任务"""
    success = scheduler_service.run_job_now(job_id)
    if success:
        return {"message": f"任务 {job_id} 已触发执行"}
    else:
        return {"error": f"任务 {job_id} 不存在"}


@router.get("/status")
async def get_scheduler_status():
    """获取调度器状态"""
    return {
        "running": scheduler_service.scheduler.running,
        "initialized": scheduler_service._initialized,
        "job_count": len(scheduler_service.scheduler.get_jobs())
    }
