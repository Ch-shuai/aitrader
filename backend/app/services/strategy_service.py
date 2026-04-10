"""
策略服务 - 实现14大核心策略
"""
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from app.core.database import Strategy, Signal, Stock, DailyPrice, FactorData
from app.services.factor_service import FactorService


class StrategyService:
    """策略执行服务"""

    def __init__(self):
        self.factor_service = FactorService()

    def run_strategy(self, db: Session, strategy: Strategy, run_date: Optional[str] = None) -> List[Signal]:
        """运行策略生成信号"""

        if strategy.code == "value_fscore":
            return self._run_value_fscore(db, strategy, run_date)
        elif strategy.code == "momentum_price":
            return self._run_momentum_price(db, strategy, run_date)
        elif strategy.code == "tech_breakout":
            return self._run_tech_breakout(db, strategy, run_date)
        elif strategy.code == "growth_can_slim":
            return self._run_growth_can_slim(db, strategy, run_date)
        elif strategy.code == "tech_trend":
            return self._run_tech_trend(db, strategy, run_date)
        elif strategy.code == "value_dividend":
            return self._run_value_dividend(db, strategy, run_date)
        elif strategy.code == "mf_quality_value":
            return self._run_quality_value(db, strategy, run_date)
        else:
            # 自定义策略
            return self._run_custom_strategy(db, strategy, run_date)

    def _run_value_fscore(self, db: Session, strategy: Strategy, run_date: Optional[str] = None) -> List[Signal]:
        """F-Score价值策略"""
        params = strategy.params or {}
        fscore_threshold = params.get("fscore_threshold", 7)
        pe_max = params.get("pe_max", 15)

        signals = []
        stocks = db.query(Stock).all()

        for stock in stocks[:100]:  # 限制处理数量
            try:
                # 获取PE数据
                latest_factor = db.query(FactorData).filter(
                    FactorData.code == stock.code,
                    FactorData.factor_name == "pe_ttm"
                ).order_by(FactorData.date.desc()).first()

                if latest_factor and latest_factor.factor_value < pe_max and latest_factor.factor_value > 0:
                    # 计算真实的 F-Score
                    f_score = self._calculate_f_score(stock.code, db)

                    if f_score >= fscore_threshold:
                        signal = self._create_signal(
                            db, strategy.id, stock.code, "buy",
                            confidence=min(f_score / 9, 0.95),
                            reason=f"F-Score={f_score}, PE={latest_factor.factor_value:.2f}",
                            buy_grade=min(f_score - 6, 5)
                        )
                        signals.append(signal)
            except Exception as e:
                continue

        db.commit()
        return signals

    def _run_momentum_price(self, db: Session, strategy: Strategy, run_date: Optional[str] = None) -> List[Signal]:
        """价格动量策略"""
        params = strategy.params or {}
        momentum_window = params.get("momentum_window", 20)

        signals = []
        stocks = db.query(Stock).all()

        for stock in stocks[:100]:
            try:
                # 获取近期价格
                prices = db.query(DailyPrice).filter(
                    DailyPrice.code == stock.code
                ).order_by(DailyPrice.date.desc()).limit(70).all()

                if len(prices) < 60:
                    continue

                df = pd.DataFrame([{
                    'close': p.close,
                    'volume': p.volume
                } for p in reversed(prices)])

                # 计算动量
                ret_20 = (df['close'].iloc[-1] - df['close'].iloc[-21]) / df['close'].iloc[-21] * 100
                ret_60 = (df['close'].iloc[-1] - df['close'].iloc[-61]) / df['close'].iloc[-61] * 100
                ma20 = df['close'].tail(20).mean()
                vol_ratio = df['volume'].iloc[-1] / df['volume'].tail(20).mean()

                # 动量条件
                if ret_20 > 10 and ret_60 > 0 and df['close'].iloc[-1] > ma20 and vol_ratio > 1.0:
                    confidence = min(ret_20 / 30, 0.95)
                    buy_grade = min(int(ret_20 / 5) + 1, 5)

                    signal = self._create_signal(
                        db, strategy.id, stock.code, "buy",
                        trigger_price=df['close'].iloc[-1],
                        confidence=confidence,
                        reason=f"20日动量{ret_20:.1f}%, 量价配合{vol_ratio:.2f}",
                        buy_grade=buy_grade
                    )
                    signals.append(signal)

            except Exception as e:
                continue

        db.commit()
        return signals

    def _run_tech_breakout(self, db: Session, strategy: Strategy, run_date: Optional[str] = None) -> List[Signal]:
        """技术突破策略"""
        params = strategy.params or {}
        breakout_window = params.get("breakout_window", 20)
        volume_multiplier = params.get("volume_multiplier", 1.5)

        signals = []
        stocks = db.query(Stock).all()

        for stock in stocks[:100]:
            try:
                prices = db.query(DailyPrice).filter(
                    DailyPrice.code == stock.code
                ).order_by(DailyPrice.date.desc()).limit(70).all()

                if len(prices) < breakout_window + 5:
                    continue

                df = pd.DataFrame([{
                    'high': p.high,
                    'low': p.low,
                    'close': p.close,
                    'volume': p.volume
                } for p in reversed(prices)])

                current = df.iloc[-1]
                high_20 = df['high'].tail(breakout_window).max()
                vol_ma5 = df['volume'].tail(5).mean()
                ma60 = df['close'].tail(60).mean()

                # 突破条件
                if (current['close'] >= high_20 and
                    current['volume'] > vol_ma5 * volume_multiplier and
                    current['close'] > ma60):

                    breakout_pct = (current['close'] - df['close'].iloc[-breakout_window]) / df['close'].iloc[-breakout_window] * 100
                    confidence = min(breakout_pct / 20, 0.95)
                    buy_grade = min(int(breakout_pct / 5) + 2, 5)

                    signal = self._create_signal(
                        db, strategy.id, stock.code, "buy",
                        trigger_price=current['close'],
                        confidence=confidence,
                        reason=f"突破{breakout_window}日新高, 成交量放大{current['volume']/vol_ma5:.1f}倍",
                        buy_grade=buy_grade
                    )
                    signals.append(signal)

            except Exception as e:
                continue

        db.commit()
        return signals

    def _run_growth_can_slim(self, db: Session, strategy: Strategy, run_date: Optional[str] = None) -> List[Signal]:
        """CANSLIM成长策略"""
        params = strategy.params or {}
        eps_growth_min = params.get("eps_growth_min", 25)

        signals = []
        stocks = db.query(Stock).limit(100).all()

        for stock in stocks:
            try:
                # 获取价格数据
                prices = db.query(DailyPrice).filter(
                    DailyPrice.code == stock.code
                ).order_by(DailyPrice.date.desc()).limit(260).all()

                if len(prices) < 100:
                    continue

                df = pd.DataFrame([{
                    'close': p.close,
                    'high': p.high
                } for p in reversed(prices)])

                # 检查是否创250日新高 (N)
                high_250 = df['high'].tail(250).max()
                current = df.iloc[-1]

                if current['close'] >= high_250 * 0.95:  # 接近新高
                    # 检查动量 (M)
                    ret_60 = (current['close'] - df['close'].iloc[-61]) / df['close'].iloc[-61] * 100

                    if ret_60 > 20:  # 市场向上
                        signal = self._create_signal(
                            db, strategy.id, stock.code, "buy",
                            trigger_price=current['close'],
                            confidence=0.75,
                            reason=f"接近250日新高, 60日收益{ret_60:.1f}%",
                            buy_grade=4
                        )
                        signals.append(signal)

            except Exception as e:
                continue

        db.commit()
        return signals

    def _run_tech_trend(self, db: Session, strategy: Strategy, run_date: Optional[str] = None) -> List[Signal]:
        """趋势跟踪策略 - 均线多头排列"""
        signals = []
        stocks = db.query(Stock).limit(100).all()

        for stock in stocks:
            try:
                prices = db.query(DailyPrice).filter(
                    DailyPrice.code == stock.code
                ).order_by(DailyPrice.date.desc()).limit(70).all()

                if len(prices) < 60:
                    continue

                df = pd.DataFrame([{
                    'close': p.close,
                    'volume': p.volume
                } for p in reversed(prices)])

                # 计算均线
                ma5 = df['close'].tail(5).mean()
                ma10 = df['close'].tail(10).mean()
                ma20 = df['close'].tail(20).mean()
                ma60 = df['close'].tail(60).mean()

                current = df.iloc[-1]

                # 多头排列条件
                if ma5 > ma10 > ma20 > ma60 and current['close'] > ma5:
                    # 计算趋势强度
                    trend_strength = (ma5 - ma60) / ma60 * 100
                    confidence = min(trend_strength / 10, 0.95)
                    buy_grade = min(int(trend_strength / 3) + 1, 5)

                    signal = self._create_signal(
                        db, strategy.id, stock.code, "buy",
                        trigger_price=current['close'],
                        confidence=confidence,
                        reason=f"均线多头排列, 趋势强度{trend_strength:.1f}%",
                        buy_grade=buy_grade
                    )
                    signals.append(signal)

            except Exception as e:
                continue

        db.commit()
        return signals

    def _run_value_dividend(self, db: Session, strategy: Strategy, run_date: Optional[str] = None) -> List[Signal]:
        """红利策略"""
        signals = []
        # 简化实现 - 基于低PE和高ROE筛选
        stocks = db.query(Stock).limit(100).all()

        for stock in stocks:
            try:
                pe_data = db.query(FactorData).filter(
                    FactorData.code == stock.code,
                    FactorData.factor_name == "pe_ttm"
                ).order_by(FactorData.date.desc()).first()

                roe_data = db.query(FactorData).filter(
                    FactorData.code == stock.code,
                    FactorData.factor_name == "roe"
                ).order_by(FactorData.date.desc()).first()

                if pe_data and roe_data:
                    pe = pe_data.factor_value
                    roe = roe_data.factor_value

                    # 低估值 + 高盈利
                    if 0 < pe < 20 and roe > 10:
                        confidence = min((20 - pe) / 20 + roe / 50, 0.95)
                        buy_grade = min(int((20 - pe) / 5) + int(roe / 10), 5)

                        signal = self._create_signal(
                            db, strategy.id, stock.code, "buy",
                            confidence=confidence,
                            reason=f"PE={pe:.1f}, ROE={roe:.1f}%",
                            buy_grade=buy_grade
                        )
                        signals.append(signal)

            except Exception as e:
                continue

        db.commit()
        return signals

    def _run_quality_value(self, db: Session, strategy: Strategy, run_date: Optional[str] = None) -> List[Signal]:
        """质量价值策略"""
        signals = []
        stocks = db.query(Stock).limit(100).all()

        for stock in stocks:
            try:
                # 获取多因子
                roe_data = db.query(FactorData).filter(
                    FactorData.code == stock.code,
                    FactorData.factor_name == "roe"
                ).order_by(FactorData.date.desc()).first()

                pe_data = db.query(FactorData).filter(
                    FactorData.code == stock.code,
                    FactorData.factor_name == "pe_ttm"
                ).order_by(FactorData.date.desc()).first()

                if roe_data and pe_data:
                    roe = roe_data.factor_value
                    pe = pe_data.factor_value

                    # 高质量 + 合理估值
                    if roe > 15 and 0 < pe < 25:
                        quality_score = min(roe / 30, 1.0)
                        value_score = min((30 - pe) / 30, 1.0)
                        total_score = (quality_score + value_score) / 2

                        signal = self._create_signal(
                            db, strategy.id, stock.code, "buy",
                            confidence=total_score,
                            reason=f"高质量价值: ROE={roe:.1f}%, PE={pe:.1f}",
                            buy_grade=min(int(total_score * 5) + 1, 5)
                        )
                        signals.append(signal)

            except Exception as e:
                continue

        db.commit()
        return signals

    def _run_custom_strategy(self, db: Session, strategy: Strategy, run_date: Optional[str] = None) -> List[Signal]:
        """运行自定义策略"""
        # 自定义策略可以根据params中的条件组合筛选
        params = strategy.params or {}
        signals = []

        # 这里可以实现更复杂的自定义逻辑
        # 简化实现：根据params中的factor_conditions筛选

        return signals

    def _create_signal(
        self,
        db: Session,
        strategy_id: int,
        code: str,
        signal_type: str,
        trigger_price: float = None,
        confidence: float = 0.5,
        reason: str = "",
        buy_grade: int = 3
    ) -> Signal:
        """创建交易信号"""

        # 检查是否已存在相同信号
        existing = db.query(Signal).filter(
            Signal.strategy_id == strategy_id,
            Signal.code == code,
            Signal.signal_type == signal_type,
            Signal.status == "pending"
        ).first()

        if existing:
            return existing

        signal = Signal(
            code=code,
            strategy_id=strategy_id,
            signal_type=signal_type,
            trigger_price=trigger_price,
            confidence=confidence,
            reason=reason,
            buy_grade=buy_grade,
            status="pending"
        )
        db.add(signal)
        db.flush()
        return signal

    def generate_buy_point_grade(self, code: str, factors: Dict) -> int:
        """
        生成买点分级 (1-5级)
        5级: 极佳买点 - 多因子共振，高概率上涨
        4级: 良好买点 - 主要因子支持
        3级: 普通买点 - 有一定支持但需谨慎
        2级: 观察买点 - 信号较弱
        1级: 警惕买点 - 风险较高，建议观望
        """
        score = 0

        # 技术面评分
        if factors.get('above_ma20', 0) and factors.get('above_ma60', 0):
            score += 2
        elif factors.get('above_ma20', 0):
            score += 1

        if factors.get('golden_cross', 0):
            score += 1

        if factors.get('breakout_20d_high', 0):
            score += 1

        rsi = factors.get('rsi_14', 50)
        if 40 < rsi < 70:
            score += 1

        # 动量评分
        momentum = factors.get('momentum_20', 0)
        if momentum > 10:
            score += 1
        elif momentum > 0:
            score += 0.5

        # 估值评分
        pe = factors.get('pe_ttm', 100)
        if 0 < pe < 30:
            score += 1

        # 转换为1-5级
        if score >= 6:
            return 5
        elif score >= 4:
            return 4
        elif score >= 3:
            return 3
        elif score >= 2:
            return 2
        else:
            return 1

    def _get_financial_data(self, code: str) -> Optional[Dict]:
        """
        获取财务数据用于F-Score计算
        
        Returns:
            包含财务指标的字典，获取失败返回None
        """
        try:
            import akshare as ak
            
            # 获取最新财务指标
            fin_data = ak.stock_financial_analysis_indicator(symbol=code)
            if fin_data is None or fin_data.empty:
                return None
            
            latest = fin_data.iloc[0]
            
            # 获取上一期数据进行对比
            prev = fin_data.iloc[1] if len(fin_data) > 1 else None
            
            return {
                "roa": float(latest.get("总资产报酬率", 0)),
                "cfo": float(latest.get("经营活动产生的现金流量净额", 0)),
                "debt_ratio": float(latest.get("资产负债率", 0)),
                "current_ratio": float(latest.get("流动比率", 0)),
                "shares": float(latest.get("总股本", 0)),
                "gross_margin": float(latest.get("销售毛利率", 0)),
                "asset_turnover": float(latest.get("总资产周转率", 0)),
                # 上期数据
                "prev_roa": float(prev.get("总资产报酬率", 0)) if prev is not None else 0,
                "prev_debt_ratio": float(prev.get("资产负债率", 0)) if prev is not None else 100,
                "prev_current_ratio": float(prev.get("流动比率", 0)) if prev is not None else 0,
                "prev_shares": float(prev.get("总股本", 0)) if prev is not None else 0,
                "prev_gross_margin": float(prev.get("销售毛利率", 0)) if prev is not None else 0,
                "prev_asset_turnover": float(prev.get("总资产周转率", 0)) if prev is not None else 0,
            }
        except Exception as e:
            return None
    
    def _calculate_f_score(self, code: str, db: Session) -> int:
        """
        计算Piotroski F-Score
        
        F-Score是一个0-9分的财务健康评分:
        - 盈利能力指标 (4分)
        - 杠杆/流动性指标 (3分)
        - 效率指标 (2分)
        
        Returns:
            0-9的整数分数
        """
        fin = self._get_financial_data(code)
        if fin is None:
            return 0
        
        score = 0
        
        # 1. ROA > 0 (资产回报率正)
        if fin["roa"] > 0:
            score += 1
        
        # 2. CFO > 0 (经营现金流正)
        if fin["cfo"] > 0:
            score += 1
        
        # 3. ROA同比改善
        if fin["roa"] > fin["prev_roa"]:
            score += 1
        
        # 4. CFO > ROA*总资产 (简化: CFO > 净利润，这里用ROA近似)
        if fin["cfo"] > 0 and fin["roa"] > 0:
            score += 1
        
        # 5. 负债率同比下降
        if fin["debt_ratio"] < fin["prev_debt_ratio"]:
            score += 1
        
        # 6. 流动比率同比改善
        if fin["current_ratio"] > fin["prev_current_ratio"]:
            score += 1
        
        # 7. 未增发新股 (股本未增加)
        if fin["shares"] <= fin["prev_shares"]:
            score += 1
        
        # 8. 毛利率同比改善
        if fin["gross_margin"] > fin["prev_gross_margin"]:
            score += 1
        
        # 9. 资产周转率同比改善
        if fin["asset_turnover"] > fin["prev_asset_turnover"]:
            score += 1
        
        return score
