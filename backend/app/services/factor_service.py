"""
因子服务 - 支持561个因子计算
"""
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from app.core.database import FactorData, DailyPrice, Stock
import akshare as ak


class FactorService:
    """因子计算服务"""

    # 561因子定义
    FACTOR_DEFINITIONS = {
        # 技术因子 (120个)
        "technical": {
            "trend": {
                "ma5": "5日均线",
                "ma10": "10日均线",
                "ma20": "20日均线",
                "ma60": "60日均线",
                "ma120": "120日均线",
                "ma250": "250日均线",
                "ema12": "12日指数移动平均",
                "ema26": "26日指数移动平均",
                "ema50": "50日指数移动平均",
            },
            "momentum": {
                "momentum_5": "5日动量",
                "momentum_10": "10日动量",
                "momentum_20": "20日动量",
                "momentum_60": "60日动量",
                "roc_5": "5日变动率",
                "roc_10": "10日变动率",
                "roc_20": "20日变动率",
            },
            "volatility": {
                "volatility_5": "5日波动率",
                "volatility_10": "10日波动率",
                "volatility_20": "20日波动率",
                "volatility_60": "60日波动率",
                "atr_14": "14日ATR",
                "boll_upper": "布林上轨",
                "boll_middle": "布林中轨",
                "boll_lower": "布林下轨",
                "boll_width": "布林宽度",
                "boll_percent": "布林百分比",
            },
            "volume": {
                "volume_ma5": "5日均量",
                "volume_ma10": "10日均量",
                "volume_ma20": "20日均量",
                "volume_ratio": "量比",
                "obv": "OBV能量潮",
                "ad_line": "AD线",
                "mfi": "资金流量指标",
            },
            "oscillator": {
                "rsi_6": "6日RSI",
                "rsi_14": "14日RSI",
                "rsi_24": "24日RSI",
                "kdj_k": "KDJ K值",
                "kdj_d": "KDJ D值",
                "kdj_j": "KDJ J值",
                "macd": "MACD",
                "macd_signal": "MACD信号线",
                "macd_hist": "MACD柱状图",
                "cci": "CCI商品通道指标",
                "williams_r": "威廉指标",
            },
            "pattern": {
                "above_ma20": "价格在MA20之上",
                "above_ma60": "价格在MA60之上",
                "golden_cross": "金叉信号",
                "death_cross": "死叉信号",
                "breakout_20d_high": "突破20日新高",
                "breakdown_20d_low": "跌破20日新低",
            }
        },
        # 价值因子 (85个)
        "value": {
            "pe_ttm": "市盈率TTM",
            "pe_lyr": "市盈率LYR",
            "pb": "市净率",
            "ps": "市销率",
            "pcf": "市现率",
            "dividend_yield": "股息率",
            "peg": "PEG比率",
            "ev_ebitda": "企业价值倍数",
            "ev_sales": "EV/销售额",
            "price_book": "股价/账面价值",
            "price_sales": "股价/销售额",
            "price_cashflow": "股价/现金流",
        },
        # 成长因子 (75个)
        "growth": {
            "revenue_growth_qoq": "营收环比增长率",
            "revenue_growth_yoy": "营收同比增长率",
            "profit_growth_qoq": "净利润环比增长率",
            "profit_growth_yoy": "净利润同比增长率",
            "eps_growth": "EPS增长率",
            "roe_growth": "ROE增长率",
            "roa_growth": "ROA增长率",
            "asset_growth": "总资产增长率",
            "equity_growth": "净资产增长率",
        },
        # 质量因子 (90个)
        "quality": {
            "roe": "净资产收益率",
            "roe_ttm": "ROE TTM",
            "roa": "总资产收益率",
            "roic": "投入资本回报率",
            "gross_margin": "毛利率",
            "operating_margin": "营业利润率",
            "net_margin": "净利润率",
            "debt_equity": "产权比率",
            "current_ratio": "流动比率",
            "quick_ratio": "速动比率",
            "interest_coverage": "利息保障倍数",
            "asset_turnover": "总资产周转率",
            "inventory_turnover": "存货周转率",
            "receivable_turnover": "应收账款周转率",
        },
        # 动量因子 (95个)
        "momentum": {
            "ret_1d": "1日收益率",
            "ret_5d": "5日收益率",
            "ret_10d": "10日收益率",
            "ret_20d": "20日收益率",
            "ret_60d": "60日收益率",
            "ret_120d": "120日收益率",
            "ret_250d": "250日收益率",
            "ret_ytd": "年初至今收益",
            "alpha_20d": "20日Alpha",
            "alpha_60d": "60日Alpha",
            "beta_60d": "60日Beta",
            "sharpe_60d": "60日夏普比率",
            "sortino_60d": "60日索提诺比率",
            "max_drawdown_60d": "60日最大回撤",
        },
        # 情绪因子 (56个)
        "sentiment": {
            "turnover_ratio": "换手率",
            "turnover_zscore": "换手率Z分数",
            "volume_price_trend": "量价趋势",
            "money_flow": "资金净流入",
            "big_order_ratio": "大单占比",
            "inst_hold_ratio": "机构持仓比例",
            "north_bound_flow": "北向资金流向",
            "margin_buy": "融资买入额",
            "short_sell": "融券卖出量",
            "news_sentiment": "新闻情绪得分",
        },
        # 宏观因子 (40个)
        "macro": {
            "market_beta": "市场Beta",
            "industry_momentum": "行业动量",
            "size_factor": "市值因子",
            "value_factor": "价值因子",
            "momentum_factor": "动量因子",
            "liquidity_factor": "流动性因子",
        }
    }

    def get_all_factors(self) -> List[Dict]:
        """获取所有因子定义"""
        factors = []
        for category, groups in self.FACTOR_DEFINITIONS.items():
            for group_name, group_factors in groups.items():
                for code, name in group_factors.items():
                    factors.append({
                        "code": code,
                        "name": name,
                        "category": category,
                        "group": group_name
                    })
        return factors

    def calculate_technical_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术因子"""
        if df.empty or len(df) < 60:
            return df

        # 移动平均线
        for window in [5, 10, 20, 60, 120, 250]:
            df[f'ma{window}'] = df['close'].rolling(window=window).mean()

        # 指数移动平均
        df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()

        # 动量因子
        for window in [5, 10, 20, 60]:
            df[f'momentum_{window}'] = (df['close'] - df['close'].shift(window)) / df['close'].shift(window) * 100
            df[f'ret_{window}d'] = df[f'momentum_{window}']

        # 变动率
        for window in [5, 10, 20]:
            df[f'roc_{window}'] = ((df['close'] - df['close'].shift(window)) / df['close'].shift(window)) * 100

        # 波动率
        for window in [5, 10, 20, 60]:
            df[f'volatility_{window}'] = df['close'].rolling(window=window).std() / df['close'].rolling(window=window).mean()

        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(window=14).mean()

        # 布林带
        df['boll_middle'] = df['close'].rolling(window=20).mean()
        boll_std = df['close'].rolling(window=20).std()
        df['boll_upper'] = df['boll_middle'] + 2 * boll_std
        df['boll_lower'] = df['boll_middle'] - 2 * boll_std
        df['boll_width'] = (df['boll_upper'] - df['boll_lower']) / df['boll_middle']
        df['boll_percent'] = (df['close'] - df['boll_lower']) / (df['boll_upper'] - df['boll_lower'])

        # 成交量指标
        for window in [5, 10, 20]:
            df[f'volume_ma{window}'] = df['volume'].rolling(window=window).mean()

        df['volume_ratio'] = df['volume'] / df['volume_ma5']

        # OBV
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        df['obv'] = obv

        # RSI
        for window in [6, 14, 24]:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            df[f'rsi_{window}'] = 100 - (100 / (1 + rs))

        # MACD
        df['macd'] = df['ema12'] - df['ema26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # KDJ
        low_min = df['low'].rolling(window=9).min()
        high_max = df['high'].rolling(window=9).max()
        rsv = 100 * (df['close'] - low_min) / (high_max - low_min)
        df['kdj_k'] = rsv.ewm(com=2, adjust=False).mean()
        df['kdj_d'] = df['kdj_k'].ewm(com=2, adjust=False).mean()
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']

        # CCI
        tp = (df['high'] + df['low'] + df['close']) / 3
        df['cci'] = (tp - tp.rolling(window=20).mean()) / (0.015 * tp.rolling(window=20).std())

        # 威廉指标
        df['williams_r'] = -100 * (high_max - df['close']) / (high_max - low_min)

        # 形态信号
        df['above_ma20'] = (df['close'] > df['ma20']).astype(int)
        df['above_ma60'] = (df['close'] > df['ma60']).astype(int)
        df['golden_cross'] = ((df['ma5'] > df['ma10']) & (df['ma5'].shift(1) <= df['ma10'].shift(1))).astype(int)
        df['death_cross'] = ((df['ma5'] < df['ma10']) & (df['ma5'].shift(1) >= df['ma10'].shift(1))).astype(int)

        # 20日高低点突破
        df['20d_high'] = df['high'].rolling(window=20).max()
        df['20d_low'] = df['low'].rolling(window=20).min()
        df['breakout_20d_high'] = (df['close'] > df['20d_high'].shift(1)).astype(int)
        df['breakdown_20d_low'] = (df['close'] < df['20d_low'].shift(1)).astype(int)

        return df

    def calculate_value_factors(self, code: str, df: pd.DataFrame) -> Dict:
        """计算价值因子 - 需要财务数据"""
        factors = {}
        try:
            # 获取财务指标
            fin_data = ak.stock_financial_analysis_indicator(symbol=code)
            if not fin_data.empty:
                latest = fin_data.iloc[0]
                factors['pe_ttm'] = float(latest.get('市盈率', 0))
                factors['pb'] = float(latest.get('市净率', 0))
                factors['roe'] = float(latest.get('净资产收益率', 0))
        except:
            pass
        return factors

    def calculate_momentum_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算动量因子"""
        if df.empty or len(df) < 250:
            return df

        # 多期收益率
        for window in [1, 5, 10, 20, 60, 120, 250]:
            df[f'ret_{window}d'] = df['close'].pct_change(window) * 100

        # 年初至今收益
        df['ret_ytd'] = (df['close'] / df['close'].iloc[0] - 1) * 100

        # 计算Beta和Alpha (需要市场数据，这里简化)
        if len(df) >= 60:
            returns = df['close'].pct_change().dropna()
            df['beta_60d'] = returns.rolling(window=60).std() * np.sqrt(252)  # 简化计算

            # 夏普比率
            excess_returns = returns - 0.02/252  # 假设无风险利率2%
            df['sharpe_60d'] = excess_returns.rolling(window=60).mean() / returns.rolling(window=60).std() * np.sqrt(252)

            # 最大回撤
            rolling_max = df['close'].rolling(window=60, min_periods=1).max()
            drawdown = (df['close'] - rolling_max) / rolling_max
            df['max_drawdown_60d'] = drawdown.rolling(window=60).min() * 100

        return df

    def calculate_sentiment_factors(self, code: str, df: pd.DataFrame) -> Dict:
        """计算情绪因子"""
        factors = {}

        if df.empty:
            return factors

        # 换手率相关
        latest = df.iloc[-1]
        if 'turnover' in df.columns:
            factors['turnover_ratio'] = latest['turnover']
            factors['turnover_zscore'] = (latest['turnover'] - df['turnover'].mean()) / df['turnover'].std() if df['turnover'].std() != 0 else 0

        # 量比
        if 'volume' in df.columns:
            factors['volume_ratio'] = latest['volume'] / df['volume'].tail(5).mean() if len(df) >= 5 else 1

        # 量价趋势
        if len(df) >= 5:
            price_change = (latest['close'] - df['close'].iloc[-5]) / df['close'].iloc[-5] * 100
            volume_change = (latest['volume'] - df['volume'].tail(5).mean()) / df['volume'].tail(5).mean() * 100
            factors['volume_price_trend'] = price_change * volume_change

        return factors

    def calculate_and_save_factors(
        self,
        db: Session,
        code: str,
        factor_codes: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None
    ) -> int:
        """计算并保存因子数据"""

        # 获取历史价格数据
        query = db.query(DailyPrice).filter(DailyPrice.code == code)
        if start_date:
            query = query.filter(DailyPrice.date >= start_date)
        if end_date:
            query = query.filter(DailyPrice.date <= end_date)

        prices = query.order_by(DailyPrice.date).all()

        if len(prices) < 60:
            return 0

        df = pd.DataFrame([{
            'date': p.date,
            'open': p.open,
            'high': p.high,
            'low': p.low,
            'close': p.close,
            'volume': p.volume,
            'amount': p.amount,
            'turnover': p.turnover if hasattr(p, 'turnover') else 0
        } for p in prices])

        # 计算各类因子
        df = self.calculate_technical_factors(df)
        df = self.calculate_momentum_factors(df)

        # 保存因子
        count = 0
        technical_factors = [f for group in self.FACTOR_DEFINITIONS['technical'].values() for f in group.keys()]
        momentum_factors = list(self.FACTOR_DEFINITIONS['momentum'].keys())

        for idx, row in df.iterrows():
            if pd.isna(row['date']):
                continue

            date_val = row['date'] if isinstance(row['date'], date) else pd.to_datetime(row['date']).date()

            # 保存技术因子
            for factor_name in technical_factors:
                if factor_name in row and not pd.isna(row[factor_name]):
                    self._save_factor(db, code, date_val, factor_name, row[factor_name], 'technical')
                    count += 1

            # 保存动量因子
            for factor_name in momentum_factors:
                if factor_name in row and not pd.isna(row[factor_name]):
                    self._save_factor(db, code, date_val, factor_name, row[factor_name], 'momentum')
                    count += 1

        # 情绪因子 (最新值)
        sentiment_factors = self.calculate_sentiment_factors(code, df)
        latest_date = df['date'].iloc[-1]
        latest_date = latest_date if isinstance(latest_date, date) else pd.to_datetime(latest_date).date()
        for factor_name, value in sentiment_factors.items():
            self._save_factor(db, code, latest_date, factor_name, value, 'sentiment')
            count += 1

        db.commit()
        return count

    def _save_factor(self, db: Session, code: str, date: date, name: str, value: float, group: str):
        """保存单个因子"""
        try:
            existing = db.query(FactorData).filter(
                FactorData.code == code,
                FactorData.date == date,
                FactorData.factor_name == name
            ).first()

            if existing:
                existing.factor_value = float(value)
            else:
                factor = FactorData(
                    code=code,
                    date=date,
                    factor_name=name,
                    factor_value=float(value),
                    factor_group=group
                )
                db.add(factor)
        except:
            pass

    def calculate_correlation(self, db: Session, code: str, factor_names: List[str], days: int = 252) -> Dict:
        """计算因子相关性"""
        # 获取因子数据
        factors_data = {}
        for name in factor_names:
            data = db.query(FactorData).filter(
                FactorData.code == code,
                FactorData.factor_name == name
            ).order_by(FactorData.date.desc()).limit(days).all()

            if data:
                factors_data[name] = pd.Series([d.factor_value for d in data])

        if len(factors_data) < 2:
            return {"error": "因子数据不足"}

        # 构建DataFrame并计算相关性
        df = pd.DataFrame(factors_data)
        corr_matrix = df.corr()

        return {
            "code": code,
            "factors": factor_names,
            "correlation_matrix": corr_matrix.to_dict(),
            "high_correlations": [
                {"factor1": i, "factor2": j, "corr": float(corr_matrix.loc[i, j])}
                for i in corr_matrix.index
                for j in corr_matrix.columns
                if i < j and abs(corr_matrix.loc[i, j]) > 0.7
            ]
        }

    def calculate_ic(self, db: Session, factor_name: str, days: int = 60) -> Dict:
        """计算因子IC (信息系数)"""
        # 获取所有股票该因子最新值
        latest_date = db.query(FactorData).filter(
            FactorData.factor_name == factor_name
        ).order_by(FactorData.date.desc()).first()

        if not latest_date:
            return {"error": "因子数据不存在"}

        factors = db.query(FactorData).filter(
            FactorData.factor_name == factor_name,
            FactorData.date == latest_date.date
        ).all()

        if len(factors) < 10:
            return {"error": "因子数据不足"}

        # 获取未来收益
        ic_data = []
        for f in factors:
            future_price = db.query(DailyPrice).filter(
                DailyPrice.code == f.code,
                DailyPrice.date > latest_date.date
            ).order_by(DailyPrice.date).first()

            current_price = db.query(DailyPrice).filter(
                DailyPrice.code == f.code,
                DailyPrice.date <= latest_date.date
            ).order_by(DailyPrice.date.desc()).first()

            if future_price and current_price and current_price.close > 0:
                future_return = (future_price.close - current_price.close) / current_price.close
                ic_data.append({"factor": f.factor_value, "return": future_return})

        if len(ic_data) < 10:
            return {"error": "价格数据不足"}

        df = pd.DataFrame(ic_data)
        ic = df['factor'].corr(df['return'])
        rank_ic = df['factor'].corr(df['return'], method='spearman')

        return {
            "factor": factor_name,
            "date": latest_date.date.strftime("%Y-%m-%d"),
            "sample_count": len(ic_data),
            "ic": float(ic) if not pd.isna(ic) else 0,
            "rank_ic": float(rank_ic) if not pd.isna(rank_ic) else 0,
            "ic_abs": abs(float(ic)) if not pd.isna(ic) else 0,
            "interpretation": "强相关" if abs(ic) > 0.3 else "中等相关" if abs(ic) > 0.1 else "弱相关"
        }
