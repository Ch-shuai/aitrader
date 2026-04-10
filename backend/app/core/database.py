"""
数据库配置
"""
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, JSON, Boolean, Text, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()


class Stock(Base):
    """股票基础信息"""
    __tablename__ = "stocks"

    code = Column(String(10), primary_key=True, comment="股票代码")
    name = Column(String(50), nullable=False, comment="股票名称")
    industry = Column(String(50), comment="所属行业")
    concept = Column(String(200), comment="概念板块")
    market = Column(String(10), comment="市场(SH/SZ/BJ)")
    list_date = Column(Date, comment="上市日期")
    total_shares = Column(Integer, comment="总股本")
    float_shares = Column(Integer, comment="流通股本")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DailyPrice(Base):
    """日线行情"""
    __tablename__ = "daily_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True, comment="股票代码")
    date = Column(Date, nullable=False, index=True, comment="交易日期")
    open = Column(Float, comment="开盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")
    close = Column(Float, comment="收盘价")
    volume = Column(Integer, comment="成交量")
    amount = Column(Float, comment="成交额")
    turnover = Column(Float, comment="换手率")
    amplitude = Column(Float, comment="振幅")
    pct_change = Column(Float, comment="涨跌幅")
    change = Column(Float, comment="涨跌额")
    created_at = Column(DateTime, default=datetime.now)


class FactorData(Base):
    """因子数据"""
    __tablename__ = "factor_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True, comment="股票代码")
    date = Column(Date, nullable=False, index=True, comment="日期")
    factor_name = Column(String(50), nullable=False, comment="因子名称")
    factor_value = Column(Float, comment="因子值")
    factor_group = Column(String(30), comment="因子组")
    created_at = Column(DateTime, default=datetime.now)


class Strategy(Base):
    """策略配置"""
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="策略名称")
    code = Column(String(50), unique=True, nullable=False, comment="策略代码")
    description = Column(Text, comment="策略描述")
    strategy_type = Column(String(30), comment="策略类型")
    params = Column(JSON, comment="策略参数")
    status = Column(String(20), default="stopped", comment="状态")
    version = Column(String(20), default="1.0.0", comment="版本")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Signal(Base):
    """交易信号"""
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, comment="股票代码")
    strategy_id = Column(Integer, ForeignKey("strategies.id"), comment="策略ID")
    signal_type = Column(String(20), comment="信号类型(buy/sell)")
    trigger_price = Column(Float, comment="触发价格")
    confidence = Column(Float, comment="置信度")
    reason = Column(Text, comment="触发理由")
    buy_grade = Column(Integer, comment="买点分级(1-5)")
    status = Column(String(20), default="pending", comment="状态")
    created_at = Column(DateTime, default=datetime.now)


class BacktestResult(Base):
    """回测结果"""
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), comment="策略ID")
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")
    initial_capital = Column(Float, comment="初始资金")
    final_capital = Column(Float, comment="最终资金")
    total_return = Column(Float, comment="总收益率")
    annual_return = Column(Float, comment="年化收益率")
    sharpe_ratio = Column(Float, comment="夏普比率")
    max_drawdown = Column(Float, comment="最大回撤")
    win_rate = Column(Float, comment="胜率")
    trade_count = Column(Integer, comment="交易次数")
    params = Column(JSON, comment="回测参数")
    created_at = Column(DateTime, default=datetime.now)


class NewsItem(Base):
    """新闻资讯"""
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), comment="标题")
    content = Column(Text, comment="内容")
    source = Column(String(50), comment="来源")
    url = Column(String(500), comment="链接")
    publish_time = Column(DateTime, comment="发布时间")
    category = Column(String(50), comment="分类")
    sentiment = Column(String(20), comment="情感倾向")
    related_stocks = Column(String(200), comment="相关股票")
    created_at = Column(DateTime, default=datetime.now)


# 数据库引擎和会话
DB_PATH = os.path.join(os.path.dirname(__file__), "../../../data/aitrader.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
