"""
数据同步服务 - 管理完整的数据同步流程
"""
from sqlalchemy.orm import Session
from typing import Dict, Optional
from datetime import datetime, date, timedelta
from app.core.database import Stock, DailyPrice, SessionLocal
from app.services.data_service import StockDataService, NewsService
from app.services.factor_service import FactorService
import logging

logger = logging.getLogger(__name__)


class SyncService:
    """数据同步服务"""

    def __init__(self):
        self.stock_service = StockDataService()
        self.news_service = NewsService()
        self.factor_service = FactorService()

    def _get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    def initialize_data(self, progress_callback=None) -> Dict:
        """
        初始化数据 - 首次运行时调用

        执行流程:
        1. 同步股票列表
        2. 同步历史行情 (默认从2014年开始)
        3. 计算因子
        4. 同步新闻

        Returns:
            同步结果统计
        """
        results = {
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "steps": []
        }

        db = self._get_db()

        try:
            # Step 1: 同步股票列表
            logger.info("[初始化] 步骤 1/4: 同步股票列表...")
            if progress_callback:
                progress_callback("同步股票列表", 1, 4)

            stock_count = self.stock_service.sync_stock_list(db)
            results["steps"].append({
                "step": 1,
                "name": "同步股票列表",
                "status": "success",
                "count": stock_count
            })
            logger.info(f"[初始化] 股票列表同步完成: {stock_count} 只")

            # Step 2: 同步历史行情
            logger.info("[初始化] 步骤 2/4: 同步历史行情...")
            if progress_callback:
                progress_callback("同步历史行情", 2, 4)

            # 只同步部分活跃股票的历史数据 (避免首次运行时间过长)
            stocks = db.query(Stock).limit(100).all()  # 先同步前100只
            price_count = 0
            for i, stock in enumerate(stocks):
                try:
                    count = self.stock_service.sync_daily_prices(db, stock.code)
                    price_count += count
                    if (i + 1) % 10 == 0:
                        logger.info(f"[初始化] 已同步 {i + 1}/{len(stocks)} 只股票行情")
                except Exception as e:
                    logger.error(f"[初始化] 同步 {stock.code} 行情失败: {e}")

            results["steps"].append({
                "step": 2,
                "name": "同步历史行情",
                "status": "success",
                "count": price_count
            })
            logger.info(f"[初始化] 历史行情同步完成: {price_count} 条记录")

            # Step 3: 计算因子
            logger.info("[初始化] 步骤 3/4: 计算因子...")
            if progress_callback:
                progress_callback("计算因子", 3, 4)

            factor_count = 0
            for i, stock in enumerate(stocks):
                try:
                    count = self.factor_service.calculate_and_save_factors(db, stock.code)
                    factor_count += count
                    if (i + 1) % 10 == 0:
                        logger.info(f"[初始化] 已计算 {i + 1}/{len(stocks)} 只股票因子")
                except Exception as e:
                    logger.error(f"[初始化] 计算 {stock.code} 因子失败: {e}")

            results["steps"].append({
                "step": 3,
                "name": "计算因子",
                "status": "success",
                "count": factor_count
            })
            logger.info(f"[初始化] 因子计算完成: {factor_count} 条记录")

            # Step 4: 同步新闻
            logger.info("[初始化] 步骤 4/4: 同步新闻...")
            if progress_callback:
                progress_callback("同步新闻", 4, 4)

            news_count = self.news_service.fetch_news(db, limit=100)
            results["steps"].append({
                "step": 4,
                "name": "同步新闻",
                "status": "success",
                "count": news_count
            })
            logger.info(f"[初始化] 新闻同步完成: {news_count} 条")

            results["status"] = "success"
            results["end_time"] = datetime.now().isoformat()

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"[初始化] 失败: {e}")
        finally:
            db.close()

        return results

    def daily_update(self) -> Dict:
        """
        每日增量更新

        执行流程:
        1. 增量更新股票列表 (新增股票)
        2. 增量更新日线行情 (最新日期)
        3. 增量计算因子
        4. 同步新闻

        Returns:
            更新结果统计
        """
        results = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "steps": []
        }

        db = self._get_db()

        try:
            # Step 1: 增量更新股票列表
            logger.info("[每日更新] 步骤 1/4: 更新股票列表...")
            stock_count = self.stock_service.sync_stock_list(db)
            results["steps"].append({
                "step": 1,
                "name": "更新股票列表",
                "count": stock_count
            })

            # Step 2: 增量更新行情 (只更新最近5天的数据)
            logger.info("[每日更新] 步骤 2/4: 更新日线行情...")
            stocks = db.query(Stock).all()
            price_count = 0

            for stock in stocks:
                try:
                    # 只同步最近5天的数据
                    count = self._sync_recent_prices(db, stock.code, days=5)
                    price_count += count
                except Exception as e:
                    logger.error(f"[每日更新] 更新 {stock.code} 行情失败: {e}")

            results["steps"].append({
                "step": 2,
                "name": "更新日线行情",
                "count": price_count
            })

            # Step 3: 增量计算因子
            logger.info("[每日更新] 步骤 3/4: 计算因子...")
            # 只计算最近有行情更新的股票
            recent_stocks = self._get_recent_updated_stocks(db)
            factor_count = 0

            for stock_code in recent_stocks:
                try:
                    count = self.factor_service.calculate_and_save_factors(db, stock_code)
                    factor_count += count
                except Exception as e:
                    logger.error(f"[每日更新] 计算 {stock_code} 因子失败: {e}")

            results["steps"].append({
                "step": 3,
                "name": "计算因子",
                "count": factor_count
            })

            # Step 4: 同步新闻
            logger.info("[每日更新] 步骤 4/4: 同步新闻...")
            news_count = self.news_service.fetch_news(db, limit=50)
            results["steps"].append({
                "step": 4,
                "name": "同步新闻",
                "count": news_count
            })

            results["status"] = "success"
            results["end_time"] = datetime.now().isoformat()

            logger.info(f"[每日更新] 完成: 股票+{stock_count}, 行情+{price_count}, 因子+{factor_count}, 新闻+{news_count}")

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"[每日更新] 失败: {e}")
        finally:
            db.close()

        return results

    def _sync_recent_prices(self, db: Session, code: str, days: int = 5) -> int:
        """同步最近N天的行情数据"""
        import akshare as ak
        from datetime import datetime, timedelta

        # 获取最新的本地数据日期
        latest_local = db.query(DailyPrice).filter(
            DailyPrice.code == code
        ).order_by(DailyPrice.date.desc()).first()

        if latest_local:
            start_date = (latest_local.date - timedelta(days=5)).strftime("%Y%m%d")
        else:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

        end_date = datetime.now().strftime("%Y%m%d")

        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )

            count = 0
            for _, row in df.iterrows():
                import pandas as pd
                date_val = pd.to_datetime(row["日期"]).date()

                # 检查是否已存在
                existing = db.query(DailyPrice).filter(
                    DailyPrice.code == code,
                    DailyPrice.date == date_val
                ).first()

                if existing:
                    # 更新现有记录
                    existing.open = float(row["开盘"])
                    existing.high = float(row["最高"])
                    existing.low = float(row["最低"])
                    existing.close = float(row["收盘"])
                    existing.volume = int(row["成交量"])
                    existing.amount = float(row["成交额"])
                    existing.turnover = float(row.get("换手率", 0))
                    existing.pct_change = float(row.get("涨跌幅", 0))
                else:
                    # 插入新记录
                    price = DailyPrice(
                        code=code,
                        date=date_val,
                        open=float(row["开盘"]),
                        high=float(row["最高"]),
                        low=float(row["最低"]),
                        close=float(row["收盘"]),
                        volume=int(row["成交量"]),
                        amount=float(row["成交额"]),
                        turnover=float(row.get("换手率", 0)),
                        pct_change=float(row.get("涨跌幅", 0)),
                    )
                    db.add(price)
                    count += 1

            db.commit()
            return count

        except Exception as e:
            logger.error(f"同步 {code} 近期行情失败: {e}")
            return 0

    def _get_recent_updated_stocks(self, db: Session) -> list:
        """获取最近有数据更新的股票列表"""
        from datetime import datetime, timedelta

        recent_date = datetime.now().date() - timedelta(days=2)

        recent_prices = db.query(DailyPrice.code).filter(
            DailyPrice.date >= recent_date
        ).distinct().all()

        return [p.code for p in recent_prices]

    def get_sync_status(self) -> Dict:
        """获取数据同步状态"""
        db = self._get_db()

        try:
            # 统计各类数据
            stock_count = db.query(Stock).count()
            price_count = db.query(DailyPrice).count()
            factor_count = db.query(FactorService).count() if hasattr(FactorService, '__tablename__') else 0

            # 获取最新数据日期
            latest_price = db.query(DailyPrice).order_by(DailyPrice.date.desc()).first()

            return {
                "status": "ok",
                "statistics": {
                    "stocks": stock_count,
                    "prices": price_count,
                    "latest_date": latest_price.date.strftime("%Y-%m-%d") if latest_price else None
                }
            }
        finally:
            db.close()


# 全局同步服务实例
sync_service = SyncService()
