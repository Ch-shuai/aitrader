"""
机器学习服务 - XGBoost预测模型
"""
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date, timedelta
from app.core.database import Stock, DailyPrice, FactorData
import logging

logger = logging.getLogger(__name__)

# 尝试导入ML库
try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    ML_AVAILABLE = True
except ImportError:
    logger.warning("ML库未安装，机器学习功能不可用")
    ML_AVAILABLE = False


class MLService:
    """机器学习预测服务"""

    def __init__(self):
        self.models = {}  # 缓存已训练的模型
        self.feature_cols = [
            'ma5', 'ma10', 'ma20', 'ma60',
            'rsi_14', 'macd',
            'momentum_20', 'volatility_20',
            'volume_ratio', 'turnover_ratio'
        ]

    def prepare_training_data(
        self,
        db: Session,
        code: str,
        lookback_days: int = 60,
        prediction_days: int = 5
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        准备训练数据

        Args:
            code: 股票代码
            lookback_days: 回看天数
            prediction_days: 预测未来天数

        Returns:
            X: 特征DataFrame
            y: 标签Series (1: 上涨, 0: 下跌)
        """
        # 获取历史价格
        prices = db.query(DailyPrice).filter(
            DailyPrice.code == code
        ).order_by(DailyPrice.date).all()

        if len(prices) < lookback_days + prediction_days + 20:
            return None, None

        df = pd.DataFrame([{
            'date': p.date,
            'open': p.open,
            'high': p.high,
            'low': p.low,
            'close': p.close,
            'volume': p.volume,
            'turnover': p.turnover if hasattr(p, 'turnover') else 0
        } for p in prices])

        # 计算技术指标
        df = self._calculate_features(df)

        # 获取因子数据
        factors = db.query(FactorData).filter(
            FactorData.code == code,
            FactorData.factor_name.in_(self.feature_cols)
        ).all()

        # 合并因子数据
        factor_df = pd.DataFrame([
            {'date': f.date, f.factor_name: f.factor_value}
            for f in factors
        ])

        if not factor_df.empty:
            factor_df = factor_df.groupby('date').first().reset_index()
            df = df.merge(factor_df, on='date', how='left')

        # 创建标签: N天后是否上涨
        df['future_return'] = df['close'].shift(-prediction_days) / df['close'] - 1
        df['label'] = (df['future_return'] > 0).astype(int)

        # 删除缺失值
        df = df.dropna()

        if len(df) < 50:
            return None, None

        # 构建特征矩阵
        feature_cols = [c for c in self.feature_cols if c in df.columns]
        feature_cols.extend(['close', 'volume'])  # 基础特征

        X = df[feature_cols].fillna(0)
        y = df['label']

        return X, y

    def _calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标特征"""
        # 移动平均线
        for window in [5, 10, 20, 60]:
            df[f'ma{window}'] = df['close'].rolling(window=window).mean()

        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2

        # 动量
        df['momentum_20'] = df['close'].pct_change(20)

        # 波动率
        df['volatility_20'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()

        # 成交量相关
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma5']

        return df

    def train_model(
        self,
        db: Session,
        code: str,
        model_type: str = 'xgboost'
    ) -> Dict:
        """
        训练预测模型

        Returns:
            训练结果和模型性能指标
        """
        if not ML_AVAILABLE:
            return {"error": "ML库未安装"}

        X, y = self.prepare_training_data(db, code)

        if X is None or len(X) < 100:
            return {"error": "数据不足，无法训练模型"}

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )

        # 训练模型
        if model_type == 'xgboost':
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:
            return {"error": f"不支持的模型类型: {model_type}"}

        model.fit(X_train, y_train)

        # 评估模型
        y_pred = model.predict(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)

        # 保存模型
        self.models[code] = {
            'model': model,
            'feature_cols': list(X.columns),
            'metrics': {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall
            }
        }

        # 特征重要性
        importance = dict(zip(X.columns, model.feature_importances_))

        return {
            "code": code,
            "model_type": model_type,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "feature_importance": dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5])
        }

    def predict(
        self,
        db: Session,
        code: str,
        days_ahead: int = 5
    ) -> Dict:
        """
        预测未来走势

        Returns:
            预测结果
        """
        if not ML_AVAILABLE:
            return {"error": "ML库未安装"}

        # 检查是否有缓存模型
        if code not in self.models:
            # 自动训练模型
            result = self.train_model(db, code)
            if "error" in result:
                return result

        model_info = self.models[code]
        model = model_info['model']
        feature_cols = model_info['feature_cols']

        # 准备最新数据
        prices = db.query(DailyPrice).filter(
            DailyPrice.code == code
        ).order_by(DailyPrice.date.desc()).limit(70).all()

        if len(prices) < 60:
            return {"error": "历史数据不足"}

        df = pd.DataFrame([{
            'date': p.date,
            'open': p.open,
            'high': p.high,
            'low': p.low,
            'close': p.close,
            'volume': p.volume
        } for p in reversed(prices)])

        df = self._calculate_features(df)

        # 获取最新特征
        latest_features = df[feature_cols].iloc[-1:].fillna(0)

        # 预测
        prediction = model.predict(latest_features)[0]
        probability = model.predict_proba(latest_features)[0]

        # 判断趋势强度
        trend_strength = abs(probability[1] - 0.5) * 2  # 0-1之间

        return {
            "code": code,
            "prediction": "上涨" if prediction == 1 else "下跌",
            "confidence": round(max(probability), 4),
            "up_probability": round(probability[1], 4),
            "trend_strength": round(trend_strength, 4),
            "model_accuracy": round(model_info['metrics']['accuracy'], 4),
            "factors": {
                "recent_return": round(df['close'].pct_change(20).iloc[-1] * 100, 2),
                "rsi": round(df['rsi_14'].iloc[-1], 2) if 'rsi_14' in df.columns else None,
                "volatility": round(df['volatility_20'].iloc[-1] * 100, 2) if 'volatility_20' in df.columns else None
            }
        }

    def batch_train(self, db: Session, max_stocks: int = 50) -> Dict:
        """
        批量训练多只股票模型

        Returns:
            训练结果统计
        """
        if not ML_AVAILABLE:
            return {"error": "ML库未安装"}

        stocks = db.query(Stock).limit(max_stocks).all()

        results = {
            "total": len(stocks),
            "success": 0,
            "failed": 0,
            "models": []
        }

        for stock in stocks:
            try:
                result = self.train_model(db, stock.code)
                if "error" not in result:
                    results["success"] += 1
                    results["models"].append({
                        "code": stock.code,
                        "accuracy": result["accuracy"]
                    })
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"训练 {stock.code} 模型失败: {e}")
                results["failed"] += 1

        return results

    def get_model_performance(self, code: Optional[str] = None) -> Dict:
        """获取模型性能报告"""
        if code:
            if code in self.models:
                return {
                    "code": code,
                    "metrics": self.models[code]['metrics'],
                    "status": "trained"
                }
            else:
                return {"error": f"股票 {code} 的模型未训练"}

        # 返回所有模型概览
        return {
            "total_models": len(self.models),
            "models": [
                {
                    "code": code,
                    "accuracy": info['metrics']['accuracy']
                }
                for code, info in self.models.items()
            ]
        }


# 全局ML服务实例
ml_service = MLService()
