"""
定时任务调度服务 - 使用 APScheduler
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import datetime, time
from app.core.database import SessionLocal
from app.services.data_service import StockDataService, NewsService
from app.services.factor_service import FactorService
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务服务"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.stock_service = StockDataService()
        self.news_service = NewsService()
        self.factor_service = FactorService()
        self._initialized = False

    def init_scheduler(self):
        """初始化定时任务"""
        if self._initialized:
            return

        # 每日 15:30 同步股票列表 (收盘后)
        self.scheduler.add_job(
            self._sync_stock_list_job,
            CronTrigger(hour=15, minute=30),
            id='sync_stock_list',
            name='同步股票列表',
            replace_existing=True
        )

        # 每日 15:45 同步日线行情 (收盘后)
        self.scheduler.add_job(
            self._sync_daily_prices_job,
            CronTrigger(hour=15, minute=45),
            id='sync_daily_prices',
            name='同步日线行情',
            replace_existing=True
        )

        # 每日 16:00 计算因子 (数据同步完成后)
        self.scheduler.add_job(
            self._calculate_factors_job,
            CronTrigger(hour=16, minute=0),
            id='calculate_factors',
            name='计算因子',
            replace_existing=True
        )

        # 每小时同步一次新闻
        self.scheduler.add_job(
            self._sync_news_job,
            CronTrigger(minute=0),  # 每小时的第0分钟
            id='sync_news',
            name='同步新闻',
            replace_existing=True
        )

        # 每周一 9:00 清理过期数据
        self.scheduler.add_job(
            self._cleanup_job,
            CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='cleanup',
            name='清理过期数据',
            replace_existing=True
        )

        self._initialized = True
        logger.info("定时任务初始化完成")

    def start(self):
        """启动调度器"""
        self.init_scheduler()
        self.scheduler.start()
        logger.info("定时任务调度器已启动")

    def shutdown(self):
        """关闭调度器"""
        self.scheduler.shutdown()
        logger.info("定时任务调度器已关闭")

    def _get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    async def _sync_stock_list_job(self):
        """同步股票列表任务"""
        logger.info("[定时任务] 开始同步股票列表...")
        db = self._get_db()
        try:
            count = self.stock_service.sync_stock_list(db)
            logger.info(f"[定时任务] 股票列表同步完成，新增 {count} 只股票")
        except Exception as e:
            logger.error(f"[定时任务] 同步股票列表失败: {e}")
        finally:
            db.close()

    async def _sync_daily_prices_job(self):
        """同步日线行情任务"""
        logger.info("[定时任务] 开始同步日线行情...")
        db = self._get_db()
        try:
            count = self.stock_service.sync_daily_prices(db)
            logger.info(f"[定时任务] 日线行情同步完成，新增 {count} 条记录")
        except Exception as e:
            logger.error(f"[定时任务] 同步日线行情失败: {e}")
        finally:
            db.close()

    async def _calculate_factors_job(self):
        """计算因子任务"""
        logger.info("[定时任务] 开始计算因子...")
        db = self._get_db()
        try:
            # 获取所有股票
            from app.core.database import Stock
            stocks = db.query(Stock).all()
            total_count = 0

            for i, stock in enumerate(stocks):
                try:
                    count = self.factor_service.calculate_and_save_factors(db, stock.code)
                    total_count += count

                    # 每处理 50 只股票记录一次日志
                    if (i + 1) % 50 == 0:
                        logger.info(f"[定时任务] 已处理 {i + 1}/{len(stocks)} 只股票")

                except Exception as e:
                    logger.error(f"[定时任务] 计算 {stock.code} 因子失败: {e}")
                    continue

            logger.info(f"[定时任务] 因子计算完成，共 {total_count} 条记录")
        except Exception as e:
            logger.error(f"[定时任务] 计算因子失败: {e}")
        finally:
            db.close()

    async def _sync_news_job(self):
        """同步新闻任务"""
        logger.info("[定时任务] 开始同步新闻...")
        db = self._get_db()
        try:
            count = self.news_service.fetch_news(db, limit=100)
            logger.info(f"[定时任务] 新闻同步完成，新增 {count} 条新闻")
        except Exception as e:
            logger.error(f"[定时任务] 同步新闻失败: {e}")
        finally:
            db.close()

    async def _cleanup_job(self):
        """清理过期数据任务"""
        logger.info("[定时任务] 开始清理过期数据...")
        db = self._get_db()
        try:
            # 清理过期信号 (30天前)
            from datetime import datetime, timedelta
            from app.core.database import Signal

            cutoff_date = datetime.now() - timedelta(days=30)
            expired_signals = db.query(Signal).filter(
                Signal.created_at < cutoff_date,
                Signal.status == 'pending'
            ).all()

            count = 0
            for signal in expired_signals:
                signal.status = 'expired'
                count += 1

            db.commit()
            logger.info(f"[定时任务] 清理完成，标记 {count} 条过期信号")
        except Exception as e:
            logger.error(f"[定时任务] 清理过期数据失败: {e}")
        finally:
            db.close()

    def get_jobs(self):
        """获取所有任务"""
        jobs = self.scheduler.get_jobs()
        result = []
        for job in jobs:
            try:
                next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else None
            except:
                next_run = None
            result.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": next_run,
                "trigger": str(job.trigger)
            })
        return result

    def run_job_now(self, job_id: str):
        """立即运行某个任务"""
        job = self.scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=datetime.now())
            return True
        return False


# 全局调度器实例
scheduler_service = SchedulerService()
