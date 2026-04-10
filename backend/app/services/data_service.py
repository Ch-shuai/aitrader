"""
数据服务 - 负责数据采集、清洗、存储
"""
import akshare as ak
import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import Stock, DailyPrice, NewsItem
from app.core.config import settings
import httpx
from bs4 import BeautifulSoup
import json


class StockDataService:
    """股票数据服务"""

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)

    def sync_stock_list(self, db: Session) -> int:
        """同步A股股票列表"""
        try:
            df = ak.stock_zh_a_spot_em()
            count = 0
            for _, row in df.iterrows():
                stock = db.query(Stock).filter(Stock.code == row["代码"]).first()
                if not stock:
                    stock = Stock(
                        code=row["代码"],
                        name=row["名称"],
                        industry=row.get("所属行业", ""),
                        market="SH" if row["代码"].startswith("6") else "SZ",
                    )
                    db.add(stock)
                    count += 1
            db.commit()
            return count
        except Exception as e:
            print(f"同步股票列表失败: {e}")
            return 0

    def sync_daily_prices(self, db: Session, code: Optional[str] = None) -> int:
        """同步日线行情"""
        stocks = db.query(Stock).all() if not code else [db.query(Stock).filter(Stock.code == code).first()]
        count = 0

        for stock in stocks:
            if not stock:
                continue
            try:
                df = ak.stock_zh_a_hist(
                    symbol=stock.code,
                    period="daily",
                    start_date="20140101",
                    end_date=datetime.now().strftime("%Y%m%d"),
                    adjust="qfq"
                )

                for _, row in df.iterrows():
                    date_val = pd.to_datetime(row["日期"]).date()
                    price = db.query(DailyPrice).filter(
                        DailyPrice.code == stock.code,
                        DailyPrice.date == date_val
                    ).first()

                    if not price:
                        price = DailyPrice(
                            code=stock.code,
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
            except Exception as e:
                print(f"同步{stock.code}行情失败: {e}")

        return count

    def get_stock_data(self, db: Session, code: str, days: int = 252) -> pd.DataFrame:
        """获取股票历史数据"""
        prices = db.query(DailyPrice).filter(
            DailyPrice.code == code
        ).order_by(DailyPrice.date.desc()).limit(days).all()

        if not prices:
            return pd.DataFrame()

        df = pd.DataFrame([{
            "date": p.date,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "volume": p.volume,
            "amount": p.amount,
        } for p in reversed(prices)])

        return df


class NewsService:
    """资讯服务"""

    def __init__(self):
        self.sources = {
            "eastmoney": "东方财富",
            "sina": "新浪财经",
            "10jqka": "同花顺",
        }

    def fetch_news(self, db: Session, keyword: str = None, limit: int = 100) -> int:
        """抓取财经新闻"""
        count = 0
        try:
            # 东方财富新闻
            df = ak.stock_news_em()
            for _, row in df.head(limit).iterrows():
                news = db.query(NewsItem).filter(NewsItem.title == row["标题"]).first()
                if not news:
                    news = NewsItem(
                        title=row["标题"],
                        content=row.get("内容", ""),
                        source="东方财富",
                        url=row.get("链接", ""),
                        publish_time=pd.to_datetime(row["发布时间"]) if "发布时间" in row else datetime.now(),
                        category=row.get("分类", "财经"),
                    )
                    db.add(news)
                    count += 1
            db.commit()
        except Exception as e:
            print(f"抓取新闻失败: {e}")

        return count

    def get_news(self, db: Session, category: str = None, limit: int = 50) -> List[NewsItem]:
        """获取新闻列表"""
        query = db.query(NewsItem)
        if category:
            query = query.filter(NewsItem.category == category)
        return query.order_by(NewsItem.publish_time.desc()).limit(limit).all()
