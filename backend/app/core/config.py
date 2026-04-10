"""
全局配置
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    PROJECT_NAME: str = "A股智能研究与交易平台"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # API配置
    API_V1_STR: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["*"]

    # 数据库配置
    DATABASE_URL: str = "sqlite:///data/aitrader.db"

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI配置
    ANTHROPIC_API_KEY: str = ""

    # 数据源配置
    AKSHARE_ENABLE: bool = True
    TUSHARE_TOKEN: str = ""

    # 数据路径
    DATA_DIR: str = "data"
    RAW_DATA_DIR: str = "data/raw"
    PROCESSED_DATA_DIR: str = "data/processed"
    MODEL_DIR: str = "models"

    # 回测配置
    BACKTEST_START_DATE: str = "20140101"
    BACKTEST_END_DATE: str = "20241231"
    INITIAL_CAPITAL: float = 1000000.0

    # 风控配置
    MAX_POSITION_PCT: float = 0.3  # 单票最大仓位
    MAX_DRAWDOWN_PCT: float = 0.15  # 最大回撤
    STOP_LOSS_PCT: float = 0.07  # 止损线

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
