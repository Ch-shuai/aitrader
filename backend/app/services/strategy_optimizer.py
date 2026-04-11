"""
策略自优化系统 - 基于历史数据回测优化策略参数
"""
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from app.core.database import Stock, DailyPrice, Strategy, BacktestResult
from app.services.backtest_service import BacktestService
from app.core.logger import log_operation, log_backtest_result, strategy_logger


@dataclass
class ParameterRange:
    """参数范围定义"""
    name: str
    min_val: float
    max_val: float
    step: float
    dtype: str = "int"  # int, float


@dataclass
class OptimizationResult:
    """优化结果"""
    strategy_id: int
    best_params: Dict[str, Any]
    best_score: float
    all_results: List[Dict]
    optimization_time: float


class StrategyOptimizer:
    """策略优化器"""

    def __init__(self, db: Session):
        self.db = db
        self.backtest_service = BacktestService()

    def get_strategy_param_ranges(self, strategy_type: str, strategy_code: str = None) -> List[ParameterRange]:
        """获取策略参数范围"""
        param_configs = {
            "ma_cross": [
                ParameterRange("short_ma", 3, 20, 1, "int"),
                ParameterRange("long_ma", 20, 120, 5, "int"),
            ],
            "rsi": [
                ParameterRange("rsi_period", 6, 24, 2, "int"),
                ParameterRange("oversold", 20, 40, 5, "int"),
                ParameterRange("overbought", 60, 80, 5, "int"),
            ],
            "macd": [
                ParameterRange("fast", 8, 16, 2, "int"),
                ParameterRange("slow", 20, 30, 2, "int"),
                ParameterRange("signal", 7, 12, 1, "int"),
            ],
            "bollinger": [
                ParameterRange("period", 10, 30, 5, "int"),
                ParameterRange("std_dev", 1.5, 3.0, 0.5, "float"),
            ],
            "momentum": [
                ParameterRange("lookback", 10, 60, 10, "int"),
                ParameterRange("threshold", 0.02, 0.1, 0.02, "float"),
            ],
        }
        # 首先尝试根据strategy_code获取
        if strategy_code and strategy_code in param_configs:
            return param_configs[strategy_code]
        # 然后根据strategy_type获取，默认为ma_cross
        return param_configs.get(strategy_type, param_configs.get("ma_cross", []))

    def generate_param_combinations(self, param_ranges: List[ParameterRange]) -> List[Dict]:
        """生成参数组合"""
        if not param_ranges:
            return [{}]

        import itertools

        param_values = []
        for param in param_ranges:
            if param.dtype == "int":
                values = list(range(int(param.min_val), int(param.max_val) + 1, int(param.step)))
            else:
                values = [param.min_val + i * param.step
                         for i in range(int((param.max_val - param.min_val) / param.step) + 1)]
            param_values.append((param.name, values))

        combinations = []
        for combo in itertools.product(*[v for _, v in param_values]):
            combinations.append(dict(zip([n for n, _ in param_values], combo)))

        return combinations

    @log_operation("strategy_optimize", "strategy")
    def optimize_strategy(
        self,
        strategy_id: int,
        start_date: str,
        end_date: str,
        metric: str = "sharpe",  # sharpe, return, win_rate, calmar
        max_combinations: int = 50
    ) -> OptimizationResult:
        """
        优化策略参数

        Args:
            strategy_id: 策略ID
            start_date: 回测开始日期
            end_date: 回测结束日期
            metric: 优化目标指标
            max_combinations: 最大参数组合数

        Returns:
            优化结果
        """
        start_time = datetime.utcnow()

        # 获取策略信息
        strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            return OptimizationResult(
                strategy_id=strategy_id,
                best_params={},
                best_score=0,
                all_results=[],
                optimization_time=0
            )

        # 获取参数范围
        param_ranges = self.get_strategy_param_ranges(strategy.strategy_type, strategy.code)
        if not param_ranges:
            return OptimizationResult(
                strategy_id=strategy_id,
                best_params=strategy.params or {},
                best_score=0,
                all_results=[],
                optimization_time=0
            )

        # 生成参数组合
        all_combinations = self.generate_param_combinations(param_ranges)

        # 限制组合数
        if len(all_combinations) > max_combinations:
            import random
            random.seed(42)
            all_combinations = random.sample(all_combinations, max_combinations)

        strategy_logger.log_operation(
            operation="optimization_start",
            entity_type="strategy",
            entity_id=str(strategy_id),
            params={
                "strategy_type": strategy.strategy_type,
                "combinations": len(all_combinations),
                "metric": metric
            }
        )

        # 执行回测
        results = []
        best_score = float('-inf')
        best_params = {}

        for i, params in enumerate(all_combinations):
            try:
                # 更新策略参数
                strategy.params = params
                self.db.commit()

                # 执行回测
                backtest_result = self.backtest_service.run_backtest(
                    db=self.db,
                    strategy=strategy,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=100000
                )

                if "error" in backtest_result:
                    continue

                # 提取指标
                metrics = backtest_result.get("metrics", {})
                score = self._calculate_score(metrics, metric)

                result = {
                    "params": params,
                    "score": score,
                    "metrics": metrics,
                    "backtest_id": backtest_result.get("backtest_id")
                }
                results.append(result)

                if score > best_score:
                    best_score = score
                    best_params = params.copy()

                strategy_logger.log_operation(
                    operation="optimization_iteration",
                    entity_type="strategy",
                    entity_id=str(strategy_id),
                    params={"iteration": i, "params": params, "score": score}
                )

            except Exception as e:
                strategy_logger.log_operation(
                    operation="optimization_error",
                    entity_type="strategy",
                    entity_id=str(strategy_id),
                    params={"params": params, "error": str(e)},
                    level="ERROR"
                )
                continue

        # 恢复最佳参数
        if best_params:
            strategy.params = best_params
            self.db.commit()

            log_backtest_result(
                backtest_id=results[-1].get("backtest_id", 0),
                strategy_name=strategy.name,
                metrics={"best_score": best_score, "best_params": best_params}
            )

        optimization_time = (datetime.utcnow() - start_time).total_seconds()

        return OptimizationResult(
            strategy_id=strategy_id,
            best_params=best_params,
            best_score=best_score,
            all_results=results,
            optimization_time=optimization_time
        )

    def _calculate_score(self, metrics: Dict, metric: str) -> float:
        """计算评分"""
        # 处理可能为字符串的数值
        def to_float(val):
            if isinstance(val, str):
                return float(val.replace('%', ''))
            return float(val) if val is not None else 0.0

        if metric == "sharpe":
            return to_float(metrics.get("sharpe_ratio", 0))
        elif metric == "return":
            return to_float(metrics.get("total_return", 0))
        elif metric == "win_rate":
            return to_float(metrics.get("win_rate", 0))
        elif metric == "calmar":
            return to_float(metrics.get("total_return", 0)) / max(
                abs(to_float(metrics.get("max_drawdown", 1))), 0.01
            )
        else:
            return to_float(metrics.get("sharpe_ratio", 0))

    def walk_forward_optimization(
        self,
        strategy_id: int,
        start_date: str,
        end_date: str,
        train_period: int = 180,  # 训练期天数
        test_period: int = 60,    # 测试期天数
        metric: str = "sharpe"
    ) -> Dict:
        """
        滚动前向优化

        Args:
            strategy_id: 策略ID
            start_date: 开始日期
            end_date: 结束日期
            train_period: 训练期天数
            test_period: 测试期天数
            metric: 优化指标

        Returns:
            滚动优化结果
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        periods = []
        current = start

        while current + timedelta(days=train_period + test_period) <= end:
            train_start = current
            train_end = current + timedelta(days=train_period)
            test_start = train_end
            test_end = min(test_start + timedelta(days=test_period), end)

            periods.append({
                "train_start": train_start.strftime("%Y-%m-%d"),
                "train_end": train_end.strftime("%Y-%m-%d"),
                "test_start": test_start.strftime("%Y-%m-%d"),
                "test_end": test_end.strftime("%Y-%m-%d"),
            })

            current += timedelta(days=test_period)

        results = []
        for period in periods:
            # 在训练期优化参数
            opt_result = self.optimize_strategy(
                strategy_id=strategy_id,
                start_date=period["train_start"],
                end_date=period["train_end"],
                metric=metric,
                max_combinations=30
            )

            # 在测试期验证
            strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()
            if strategy and opt_result.best_params:
                strategy.params = opt_result.best_params
                self.db.commit()

                test_result = self.backtest_service.run_backtest(
                    db=self.db,
                    strategy=strategy,
                    start_date=period["test_start"],
                    end_date=period["test_end"],
                    initial_capital=100000
                )

                results.append({
                    "period": period,
                    "train_score": opt_result.best_score,
                    "test_metrics": test_result.get("metrics", {}),
                    "params": opt_result.best_params
                })

        # 汇总结果
        test_returns = [r["test_metrics"].get("total_return", 0) for r in results]
        test_sharpes = [r["test_metrics"].get("sharpe_ratio", 0) for r in results]

        return {
            "periods": results,
            "avg_test_return": np.mean(test_returns) if test_returns else 0,
            "avg_test_sharpe": np.mean(test_sharpes) if test_sharpes else 0,
            "consistency": len([r for r in test_returns if r > 0]) / len(test_returns) if test_returns else 0
        }

    def auto_optimize_all_strategies(self) -> Dict:
        """自动优化所有策略"""
        strategies = self.db.query(Strategy).filter(Strategy.is_active == True).all()

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        results = {
            "optimized": [],
            "failed": [],
            "timestamp": datetime.utcnow().isoformat()
        }

        for strategy in strategies:
            try:
                opt_result = self.optimize_strategy(
                    strategy_id=strategy.id,
                    start_date=start_date,
                    end_date=end_date,
                    metric="sharpe",
                    max_combinations=30
                )

                results["optimized"].append({
                    "strategy_id": strategy.id,
                    "strategy_name": strategy.name,
                    "best_params": opt_result.best_params,
                    "best_score": opt_result.best_score
                })

            except Exception as e:
                results["failed"].append({
                    "strategy_id": strategy.id,
                    "error": str(e)
                })

        strategy_logger.log_operation(
            operation="auto_optimize_all",
            entity_type="system",
            params={
                "total": len(strategies),
                "optimized": len(results["optimized"]),
                "failed": len(results["failed"])
            }
        )

        return results


# 全局优化器实例
def get_strategy_optimizer(db: Session) -> StrategyOptimizer:
    """获取策略优化器实例"""
    return StrategyOptimizer(db)
