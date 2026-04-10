"""
市场结构服务 - 市场环境判断、主线检测、情绪监控
"""
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from app.core.database import Stock, DailyPrice, FactorData, NewsItem
import logging

logger = logging.getLogger(__name__)


class MarketService:
    """市场结构分析服务"""

    def __init__(self):
        pass

    def analyze_market_environment(self, db: Session) -> Dict:
        """
        分析当前市场环境

        Returns:
            市场环境评估
        """
        # 获取最近的市场数据
        recent_date = db.query(DailyPrice.date).order_by(DailyPrice.date.desc()).first()

        if not recent_date:
            return {"error": "无市场数据"}

        recent_date = recent_date[0]

        # 统计涨跌分布
        prices = db.query(DailyPrice).filter(
            DailyPrice.date >= recent_date - timedelta(days=20)
        ).all()

        if not prices:
            return {"error": "数据不足"}

        # 计算市场指标
        df = pd.DataFrame([{
            'code': p.code,
            'date': p.date,
            'close': p.close,
            'pct_change': p.pct_change if hasattr(p, 'pct_change') else 0
        } for p in prices])

        # 最近5日涨跌统计
        recent_5d = df[df['date'] >= recent_date - timedelta(days=5)]
        up_count = len(recent_5d[recent_5d['pct_change'] > 0])
        down_count = len(recent_5d[recent_5d['pct_change'] < 0])
        total = up_count + down_count

        up_ratio = up_count / total if total > 0 else 0.5

        # 判断市场环境
        if up_ratio > 0.6:
            environment = "强势上涨"
            sentiment = "乐观"
        elif up_ratio > 0.55:
            environment = "震荡上行"
            sentiment = "偏乐观"
        elif up_ratio > 0.45:
            environment = "震荡整理"
            sentiment = "中性"
        elif up_ratio > 0.4:
            environment = "震荡下行"
            sentiment = "偏谨慎"
        else:
            environment = "弱势下跌"
            sentiment = "悲观"

        return {
            "date": recent_date.strftime("%Y-%m-%d"),
            "environment": environment,
            "sentiment": sentiment,
            "up_ratio": round(up_ratio, 2),
            "up_count": up_count,
            "down_count": down_count,
            "recommendation": self._get_position_advice(up_ratio)
        }

    def _get_position_advice(self, up_ratio: float) -> str:
        """根据市场情况给出仓位建议"""
        if up_ratio > 0.6:
            return "重仓参与 (70-80%)"
        elif up_ratio > 0.55:
            return "中等仓位 (50-60%)"
        elif up_ratio > 0.45:
            return "轻仓观望 (30-40%)"
        elif up_ratio > 0.4:
            return "保持谨慎 (20-30%)"
        else:
            return "空仓或极低仓位 (<20%)"

    def get_sector_rotation(self, db: Session, days: int = 20) -> Dict:
        """
        检测板块轮动

        Returns:
            热点板块列表
        """
        # 按行业统计涨跌幅
        stocks = db.query(Stock).all()
        stock_industries = {s.code: s.industry for s in stocks}

        recent_date = db.query(DailyPrice.date).order_by(DailyPrice.date.desc()).first()
        if not recent_date:
            return {"error": "无数据"}

        recent_date = recent_date[0]

        # 获取N天前的价格
        start_date = recent_date - timedelta(days=days)

        prices = db.query(DailyPrice).filter(
            DailyPrice.date >= start_date
        ).all()

        industry_returns = {}
        industry_stocks = {}

        for p in prices:
            industry = stock_industries.get(p.code)
            if not industry:
                continue

            if industry not in industry_stocks:
                industry_stocks[industry] = []

            industry_stocks[industry].append({
                'code': p.code,
                'close': p.close,
                'date': p.date
            })

        # 计算每个行业的平均收益
        for industry, stocks_data in industry_stocks.items():
            df = pd.DataFrame(stocks_data)

            # 计算每只股票的区间收益
            returns = []
            for code in df['code'].unique():
                stock_df = df[df['code'] == code].sort_values('date')
                if len(stock_df) >= 2:
                    ret = (stock_df['close'].iloc[-1] / stock_df['close'].iloc[0] - 1) * 100
                    returns.append(ret)

            if returns:
                industry_returns[industry] = {
                    'avg_return': round(np.mean(returns), 2),
                    'stock_count': len(set(df['code']))
                }

        # 排序
        sorted_sectors = sorted(
            industry_returns.items(),
            key=lambda x: x[1]['avg_return'],
            reverse=True
        )

        return {
            "period_days": days,
            "hot_sectors": [
                {"name": name, **data}
                for name, data in sorted_sectors[:5]
            ],
            "cold_sectors": [
                {"name": name, **data}
                for name, data in sorted_sectors[-5:]
            ]
        }

    def get_market_sentiment(self, db: Session) -> Dict:
        """
        综合市场情绪分析

        Returns:
            情绪指标
        """
        # 1. 新闻情绪
        recent_news = db.query(NewsItem).filter(
            NewsItem.publish_time >= datetime.now() - timedelta(days=7)
        ).all()

        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for news in recent_news:
            if news.sentiment in sentiment_counts:
                sentiment_counts[news.sentiment] += 1

        total_news = sum(sentiment_counts.values())

        # 2. 技术指标情绪 (RSI分布)
        recent_factors = db.query(FactorData).filter(
            FactorData.factor_name == "rsi_14"
        ).order_by(FactorData.date.desc()).limit(500).all()

        rsi_values = [f.factor_value for f in recent_factors if f.factor_value is not None]

        if rsi_values:
            avg_rsi = np.mean(rsi_values)
            oversold = len([r for r in rsi_values if r < 30])
            overbought = len([r for r in rsi_values if r > 70])
        else:
            avg_rsi = 50
            oversold = 0
            overbought = 0

        # 综合情绪指数 (0-100)
        # 新闻情绪权重40%, 技术情绪权重60%
        if total_news > 0:
            news_score = (sentiment_counts["positive"] * 100 + sentiment_counts["neutral"] * 50) / total_news
        else:
            news_score = 50

        tech_score = 100 - avg_rsi if avg_rsi > 50 else avg_rsi

        composite_index = news_score * 0.4 + tech_score * 0.6

        return {
            "composite_index": round(composite_index, 2),
            "interpretation": self._interpret_sentiment(composite_index),
            "news_sentiment": {
                "positive": sentiment_counts["positive"],
                "neutral": sentiment_counts["neutral"],
                "negative": sentiment_counts["negative"],
                "score": round(news_score, 2)
            },
            "technical_sentiment": {
                "avg_rsi": round(avg_rsi, 2),
                "oversold_count": oversold,
                "overbought_count": overbought,
                "score": round(tech_score, 2)
            }
        }

    def _interpret_sentiment(self, index: float) -> str:
        """解读情绪指数"""
        if index >= 80:
            return "极度乐观 - 注意风险"
        elif index >= 60:
            return "乐观 - 适合持有"
        elif index >= 40:
            return "中性 - 观望为主"
        elif index >= 20:
            return "悲观 - 寻找机会"
        else:
            return "极度悲观 - 可能反弹"

    def get_risk_warning(self, db: Session, code: str) -> Dict:
        """
        个股风险预警

        Returns:
            风险警告列表
        """
        warnings = []

        # 获取最新因子
        factors = db.query(FactorData).filter(
            FactorData.code == code
        ).order_by(FactorData.date.desc()).limit(20).all()

        factor_dict = {f.factor_name: f.factor_value for f in factors}

        # 1. 估值风险
        pe = factor_dict.get("pe_ttm", 0)
        if pe > 100:
            warnings.append({"level": "high", "type": "估值过高", "message": f"PE高达{pe:.1f}倍，估值泡沫风险"})
        elif pe > 50:
            warnings.append({"level": "medium", "type": "估值偏高", "message": f"PE为{pe:.1f}倍，注意估值回调"})

        # 2. 技术风险
        rsi = factor_dict.get("rsi_14", 50)
        if rsi > 80:
            warnings.append({"level": "high", "type": "超买", "message": f"RSI={rsi:.1f}，严重超买，回调风险大"})
        elif rsi < 20:
            warnings.append({"level": "low", "type": "超卖", "message": f"RSI={rsi:.1f}，超卖状态，可能反弹"})

        # 3. 动量风险
        momentum = factor_dict.get("momentum_20", 0)
        if momentum < -20:
            warnings.append({"level": "high", "type": "下跌趋势", "message": f"20日跌幅{momentum:.1f}%，下行趋势明显"})

        # 4. 波动风险
        volatility = factor_dict.get("volatility_20", 0)
        if volatility > 0.05:
            warnings.append({"level": "medium", "type": "高波动", "message": f"波动率{volatility*100:.1f}%，注意控制风险"})

        return {
            "code": code,
            "risk_level": "high" if any(w["level"] == "high" for w in warnings) else "medium" if warnings else "low",
            "warning_count": len(warnings),
            "warnings": warnings
        }


# 全局市场服务实例
market_service = MarketService()
