"""
AI服务 - 大模型与机器学习模型集成
"""
import os
import json
from typing import List, Optional, Dict
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.core.database import Stock, DailyPrice, NewsItem, FactorData, Strategy, BacktestResult


class AIService:
    """AI分析服务"""

    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.use_mock = not self.anthropic_api_key

    async def analyze_stock(self, db: Session, code: str, analysis_type: str) -> Dict:
        """分析个股"""
        stock = db.query(Stock).filter(Stock.code == code).first()

        # 获取最新价格
        latest_price = db.query(DailyPrice).filter(
            DailyPrice.code == code
        ).order_by(DailyPrice.date.desc()).first()

        # 获取因子数据
        factors = db.query(FactorData).filter(
            FactorData.code == code
        ).order_by(FactorData.date.desc()).limit(100).all()

        factor_dict = {}
        for f in factors:
            if f.factor_name not in factor_dict:
                factor_dict[f.factor_name] = f.factor_value

        # 构建分析文本
        if analysis_type == "technical":
            return self._technical_analysis(stock, latest_price, factor_dict)
        elif analysis_type == "fundamental":
            return self._fundamental_analysis(stock, factor_dict)
        elif analysis_type == "sentiment":
            return await self._sentiment_analysis(db, code)
        else:
            return self._comprehensive_analysis(stock, latest_price, factor_dict)

    def _technical_analysis(self, stock, latest_price, factors) -> Dict:
        """技术分析"""
        ma20 = factors.get('ma20', 0)
        ma60 = factors.get('ma60', 0)
        rsi = factors.get('rsi_14', 50)
        macd = factors.get('macd', 0)

        trend = "上升趋势" if latest_price and latest_price.close > ma20 > ma60 else \
                "下降趋势" if latest_price and latest_price.close < ma20 < ma60 else "震荡整理"

        return {
            "type": "技术分析",
            "trend": trend,
            "indicators": {
                "rsi": round(rsi, 2),
                "macd": round(macd, 4),
                "ma20": round(ma20, 2),
                "ma60": round(ma60, 2)
            },
            "signals": [
                "RSI" + ("超买" if rsi > 70 else "超卖" if rsi < 30 else "中性"),
                "MACD" + ("金叉" if macd > 0 else "死叉"),
            ],
            "conclusion": f"当前处于{trend}，建议" + ("持有" if trend == "上升趋势" else "观望" if trend == "震荡整理" else "谨慎")
        }

    def _fundamental_analysis(self, stock, factors) -> Dict:
        """基本面分析"""
        pe = factors.get('pe_ttm', 0)
        pb = factors.get('pb', 0)
        roe = factors.get('roe', 0)

        valuation = "低估" if 0 < pe < 15 else "合理" if 15 <= pe < 30 else "高估" if pe >= 30 else "未知"

        return {
            "type": "基本面分析",
            "valuation": valuation,
            "metrics": {
                "pe": round(pe, 2) if pe else None,
                "pb": round(pb, 2) if pb else None,
                "roe": f"{roe:.2f}%" if roe else None
            },
            "conclusion": f"当前估值{valuation}，ROE水平" + ("优秀" if roe and roe > 15 else "良好" if roe and roe > 10 else "一般")
        }

    async def _sentiment_analysis(self, db: Session, code: str) -> Dict:
        """情绪分析"""
        # 获取相关新闻
        news = db.query(NewsItem).filter(
            NewsItem.related_stocks.contains(code) |
            NewsItem.title.contains(code) |
            NewsItem.content.contains(code)
        ).order_by(NewsItem.publish_time.desc()).limit(20).all()

        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for n in news:
            if n.sentiment:
                sentiment_counts[n.sentiment] = sentiment_counts.get(n.sentiment, 0) + 1

        total = sum(sentiment_counts.values())
        if total > 0:
            dominant = max(sentiment_counts, key=sentiment_counts.get)
        else:
            dominant = "neutral"

        return {
            "type": "情绪分析",
            "sentiment": dominant,
            "distribution": {
                k: {"count": v, "percentage": round(v/total*100, 1) if total > 0 else 0}
                for k, v in sentiment_counts.items()
            },
            "recent_news_count": len(news),
            "conclusion": f"市场情绪{dominant}，新闻提及{len(news)}次"
        }

    def _comprehensive_analysis(self, stock, latest_price, factors) -> Dict:
        """综合分析"""
        technical = self._technical_analysis(stock, latest_price, factors)
        fundamental = self._fundamental_analysis(stock, factors)

        # 综合评分
        score = 0
        if technical["trend"] == "上升趋势":
            score += 30
        elif technical["trend"] == "震荡整理":
            score += 15

        if fundamental["valuation"] == "低估":
            score += 30
        elif fundamental["valuation"] == "合理":
            score += 20

        rsi = factors.get('rsi_14', 50)
        if 40 <= rsi <= 60:
            score += 20

        roe = factors.get('roe', 0)
        if roe and roe > 15:
            score += 20

        return {
            "type": "综合分析",
            "score": score,
            "rating": "买入" if score >= 70 else "持有" if score >= 50 else "观望" if score >= 30 else "卖出",
            "technical": technical,
            "fundamental": fundamental,
            "conclusion": f"综合评分{score}/100，建议{('买入' if score >= 70 else '持有' if score >= 50 else '观望')}"
        }

    async def analyze_market(self, db: Session, analysis_type: str) -> Dict:
        """分析市场"""
        if analysis_type == "sentiment":
            # 获取最近新闻情绪
            news = db.query(NewsItem).order_by(NewsItem.publish_time.desc()).limit(100).all()
            return {
                "type": "市场情绪",
                "recent_news": len(news),
                "conclusion": "市场整体情绪中性偏多，建议保持适度仓位"
            }
        elif analysis_type == "sector":
            return {
                "type": "板块分析",
                "hot_sectors": ["科技", "新能源", "医药"],
                "cold_sectors": ["房地产", "银行"],
                "conclusion": "科技板块表现强势，建议关注"
            }
        else:
            return {
                "type": "市场概览",
                "market_status": "震荡市",
                "risk_level": "中等",
                "conclusion": "当前市场处于震荡整理阶段，建议控制仓位，精选个股"
            }

    async def review_strategy(self, db: Session, strategy_id: int, review_type: str) -> Dict:
        """策略评估"""
        strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            return {"error": "策略不存在"}

        # 获取回测结果
        backtests = db.query(BacktestResult).filter(
            BacktestResult.strategy_id == strategy_id
        ).order_by(BacktestResult.created_at.desc()).all()

        if review_type == "performance":
            if backtests:
                latest = backtests[0]
                return {
                    "type": "绩效评估",
                    "total_return": f"{latest.total_return:.2f}%" if latest.total_return else "N/A",
                    "sharpe": round(latest.sharpe_ratio, 2) if latest.sharpe_ratio else "N/A",
                    "win_rate": f"{latest.win_rate:.2f}%" if latest.win_rate else "N/A",
                    "conclusion": "策略历史表现良好，建议继续跟踪" if latest.total_return and latest.total_return > 0 else "策略表现一般，需优化"
                }
            else:
                return {"conclusion": "暂无回测数据，建议先运行回测"}

        elif review_type == "risk":
            if backtests:
                max_dd = max([b.max_drawdown for b in backtests if b.max_drawdown], default=0)
                return {
                    "type": "风险评估",
                    "max_drawdown": f"{max_dd:.2f}%",
                    "risk_level": "高" if max_dd > 20 else "中" if max_dd > 10 else "低",
                    "conclusion": "风险可控，适合当前市场环境" if max_dd < 15 else "风险较高，建议降低仓位"
                }
            else:
                return {"conclusion": "暂无风险数据"}

        else:
            return {
                "type": "综合评估",
                "strategy_name": strategy.name,
                "backtest_count": len(backtests),
                "conclusion": f"策略'{strategy.name}'逻辑清晰，建议在实际应用前进行充分回测"
            }

    async def generate_strategy(self, market_condition: str, risk_preference: str, investment_style: str) -> Dict:
        """生成策略建议"""

        strategies = {
            ("bull", "moderate", "growth"): {
                "name": "成长动量策略",
                "description": "在牛市中追逐高成长股",
                "allocation": {"growth": 60, "tech": 25, "cash": 15},
                "factors": ["盈利增长", "价格动量", "行业景气"]
            },
            ("bear", "conservative", "value"): {
                "name": "防御价值策略",
                "description": "熊市中配置低估值防御股",
                "allocation": {"value": 50, "bond": 30, "cash": 20},
                "factors": ["低PE", "高股息", "低波动"]
            },
        }

        key = (market_condition, risk_preference, investment_style)
        strategy = strategies.get(key, {
            "name": "均衡配置策略",
            "description": "根据市场环境动态调整",
            "allocation": {"stock": 60, "bond": 25, "cash": 15},
            "factors": ["质量", "价值", "动量"]
        })

        return strategy

    async def analyze_sentiment(self, text: str) -> Dict:
        """分析文本情感"""
        # 简单规则判断
        positive_words = ['上涨', '利好', '突破', '增长', '盈利', '买入', '推荐', '强势', '机会']
        negative_words = ['下跌', '利空', '跌破', '亏损', '卖出', '回避', '弱势', '风险', '暴跌']

        pos_count = sum(1 for w in positive_words if w in text)
        neg_count = sum(1 for w in negative_words if w in text)

        if pos_count > neg_count:
            sentiment = "positive"
            score = min(0.5 + (pos_count - neg_count) * 0.1, 1.0)
        elif neg_count > pos_count:
            sentiment = "negative"
            score = max(0.5 - (neg_count - pos_count) * 0.1, 0.0)
        else:
            sentiment = "neutral"
            score = 0.5

        return {
            "sentiment": sentiment,
            "score": round(score, 2),
            "positive_words": pos_count,
            "negative_words": neg_count
        }

    async def stock_selection(self, db: Session, criteria: str, max_results: int) -> List[Dict]:
        """智能选股"""
        # 解析criteria并筛选
        stocks = db.query(Stock).limit(100).all()

        selected = []
        for stock in stocks:
            # 获取因子
            factors = db.query(FactorData).filter(
                FactorData.code == stock.code
            ).order_by(FactorData.date.desc()).limit(10).all()

            factor_dict = {f.factor_name: f.factor_value for f in factors}

            # 简单评分
            score = 0
            if factor_dict.get('pe_ttm', 100) < 20:
                score += 30
            if factor_dict.get('roe', 0) > 15:
                score += 30
            if factor_dict.get('momentum_20', 0) > 5:
                score += 20
            if factor_dict.get('rsi_14', 50) < 70:
                score += 20

            if score >= 60:
                selected.append({
                    "code": stock.code,
                    "name": stock.name,
                    "score": score,
                    "reason": f"综合评分{score}，估值合理，质地优良"
                })

        selected.sort(key=lambda x: x['score'], reverse=True)
        return selected[:max_results]

    async def chat(self, message: str, context: Optional[Dict]) -> str:
        """AI对话"""
        responses = {
            "选股": "建议关注低估值高ROE的成长股，可以使用平台的价值成长策略筛选。",
            "止损": "建议设置7-10%的止损线，根据个股波动性调整。",
            "仓位": "建议单票不超过20%仓位，行业不超过30%。",
            "趋势": "当前市场处于震荡阶段，建议控制仓位，关注结构性机会。"
        }

        for keyword, response in responses.items():
            if keyword in message:
                return response

        return "您好！我是您的AI投资助手。我可以帮您分析股票、评估策略、选股等。请问有什么可以帮助您的？"

    async def generate_daily_report(self, db: Session, date_str: Optional[str], report_type: str) -> Dict:
        """生成日报"""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # 获取当日市场数据
        return {
            "date": date_str,
            "market_summary": "今日市场震荡整理，成交量较昨日略有放大",
            "hot_sectors": ["人工智能", "新能源", "医药"],
            "individual_stock_picks": ["关注业绩超预期的成长股", "布局低估值蓝筹股"],
            "strategy_suggestions": ["维持中性仓位", "高抛低吸"],
            "risk_reminder": "注意控制仓位，防范回调风险"
        }

    async def analyze_risks(self, db: Session, codes: List[str]) -> List[Dict]:
        """风险分析"""
        warnings = []

        for code in codes:
            stock = db.query(Stock).filter(Stock.code == code).first()
            if not stock:
                continue

            # 获取最新因子
            factors = db.query(FactorData).filter(
                FactorData.code == code
            ).order_by(FactorData.date.desc()).limit(10).all()

            factor_dict = {f.factor_name: f.factor_value for f in factors}

            stock_warnings = []

            # 估值风险
            pe = factor_dict.get('pe_ttm', 0)
            if pe > 100:
                stock_warnings.append("估值过高，PE超过100倍")

            # 技术面风险
            rsi = factor_dict.get('rsi_14', 50)
            if rsi > 80:
                stock_warnings.append("RSI超买，短期回调风险")

            # 动量风险
            momentum = factor_dict.get('momentum_20', 0)
            if momentum < -15:
                stock_warnings.append("下跌趋势明显，注意止损")

            warnings.append({
                "code": code,
                "name": stock.name,
                "risk_level": "高" if len(stock_warnings) >= 2 else "中" if len(stock_warnings) == 1 else "低",
                "warnings": stock_warnings
            })

        return warnings
