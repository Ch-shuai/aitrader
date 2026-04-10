"""
回测服务 - 事件驱动回测引擎
"""
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from app.core.database import BacktestResult, Strategy, Stock, DailyPrice, Signal
import itertools


class BacktestService:
    """回测引擎服务"""

    def __init__(self):
        self.initial_capital = 1000000.0
        self.position_size = 0.2
        self.stop_loss = 0.07
        self.take_profit = 0.15

    def run_backtest(
        self,
        db: Session,
        strategy: Strategy,
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000.0,
        position_size: float = 0.2,
        stop_loss: float = 0.07,
        take_profit: float = 0.15
    ) -> Dict:
        """运行回测"""

        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

        # 初始化回测状态
        capital = initial_capital
        positions = {}  # 持仓 {code: {'shares': x, 'cost': y, 'entry_date': z}}
        trades = []  # 交易记录
        equity_curve = []  # 权益曲线

        # 获取回测期间的所有交易日
        trading_days = self._get_trading_days(db, start_dt, end_dt)

        if not trading_days:
            raise ValueError("没有可用的交易日数据")

        for i, current_date in enumerate(trading_days):
            # 获取当日所有股票数据
            daily_data = self._get_daily_data(db, current_date)

            if not daily_data:
                # 记录权益曲线
                equity_curve.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "equity": capital + sum(
                        positions[code]['shares'] * daily_data.get(code, {}).get('close', 0)
                        for code in positions
                    ) if daily_data else capital
                })
                continue

            # 1. 检查持仓 - 止损止盈
            for code in list(positions.keys()):
                if code not in daily_data:
                    continue

                pos = positions[code]
                current_price = daily_data[code]['close']
                entry_price = pos['cost']

                # 计算盈亏
                pnl_pct = (current_price - entry_price) / entry_price

                # 止损
                if pnl_pct <= -stop_loss:
                    sell_value = pos['shares'] * current_price
                    capital += sell_value
                    trades.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "code": code,
                        "action": "sell",
                        "price": current_price,
                        "shares": pos['shares'],
                        "reason": "stop_loss",
                        "pnl_pct": pnl_pct * 100
                    })
                    del positions[code]

                # 止盈
                elif pnl_pct >= take_profit:
                    sell_value = pos['shares'] * current_price
                    capital += sell_value
                    trades.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "code": code,
                        "action": "sell",
                        "price": current_price,
                        "shares": pos['shares'],
                        "reason": "take_profit",
                        "pnl_pct": pnl_pct * 100
                    })
                    del positions[code]

            # 2. 获取策略信号
            signals = self._get_signals_for_date(db, strategy.id, current_date)

            # 3. 处理买入信号
            for signal in signals:
                if signal['type'] != 'buy':
                    continue
                if signal['code'] in positions:
                    continue
                if signal['code'] not in daily_data:
                    continue

                # 计算可买入数量
                invest_amount = capital * position_size
                if invest_amount < 10000:  # 最小投资金额
                    continue

                price = daily_data[signal['code']]['close']
                shares = int(invest_amount / price / 100) * 100  # 手数

                if shares < 100:
                    continue

                cost = shares * price
                capital -= cost

                positions[signal['code']] = {
                    'shares': shares,
                    'cost': price,
                    'entry_date': current_date
                }

                trades.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "code": signal['code'],
                    "action": "buy",
                    "price": price,
                    "shares": shares,
                    "reason": signal.get('reason', ''),
                    "buy_grade": signal.get('buy_grade', 3)
                })

            # 记录权益曲线
            current_equity = capital
            for code, pos in positions.items():
                if code in daily_data:
                    current_equity += pos['shares'] * daily_data[code]['close']

            equity_curve.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "equity": current_equity,
                "cash": capital,
                "positions": len(positions)
            })

        # 计算回测指标
        final_capital = equity_curve[-1]['equity'] if equity_curve else initial_capital

        metrics = self._calculate_metrics(
            initial_capital, final_capital, trades, equity_curve, start_dt, end_dt
        )

        # 保存回测结果
        backtest_result = BacktestResult(
            strategy_id=strategy.id,
            start_date=start_dt,
            end_date=end_dt,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=metrics['total_return'],
            annual_return=metrics['annual_return'],
            sharpe_ratio=metrics['sharpe_ratio'],
            max_drawdown=metrics['max_drawdown'],
            win_rate=metrics['win_rate'],
            trade_count=len([t for t in trades if t['action'] == 'sell']),
            params={
                "trades": trades,
                "equity_curve": equity_curve,
                "position_size": position_size,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
        )
        db.add(backtest_result)
        db.commit()
        db.refresh(backtest_result)

        return {
            "id": backtest_result.id,
            "total_return": metrics['total_return'],
            "annual_return": metrics['annual_return'],
            "sharpe_ratio": metrics['sharpe_ratio'],
            "max_drawdown": metrics['max_drawdown'],
            "win_rate": metrics['win_rate'],
            "trade_count": len([t for t in trades if t['action'] == 'sell'])
        }

    def _get_trading_days(self, db: Session, start_date: date, end_date: date) -> List[date]:
        """获取交易日列表"""
        prices = db.query(DailyPrice.date).filter(
            DailyPrice.date >= start_date,
            DailyPrice.date <= end_date
        ).distinct().order_by(DailyPrice.date).all()

        return [p.date for p in prices]

    def _get_daily_data(self, db: Session, trade_date: date) -> Dict:
        """获取某日所有股票数据"""
        prices = db.query(DailyPrice).filter(DailyPrice.date == trade_date).all()

        return {
            p.code: {
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': p.close,
                'volume': p.volume
            }
            for p in prices
        }

    def _get_signals_for_date(self, db: Session, strategy_id: int, trade_date: date) -> List[Dict]:
        """获取某日的策略信号"""
        # 模拟信号生成 - 实际应调用策略逻辑
        # 这里简化处理，随机生成一些信号用于测试

        signals = []

        # 从已有的signal表中查找
        db_signals = db.query(Signal).filter(
            Signal.strategy_id == strategy_id,
            Signal.created_at >= trade_date,
            Signal.created_at < trade_date + timedelta(days=1),
            Signal.signal_type == 'buy'
        ).all()

        for s in db_signals:
            signals.append({
                'code': s.code,
                'type': s.signal_type,
                'confidence': s.confidence,
                'reason': s.reason,
                'buy_grade': s.buy_grade
            })

        return signals

    def _calculate_metrics(
        self,
        initial_capital: float,
        final_capital: float,
        trades: List[Dict],
        equity_curve: List[Dict],
        start_date: date,
        end_date: date
    ) -> Dict:
        """计算回测指标"""

        # 总收益率
        total_return = (final_capital - initial_capital) / initial_capital * 100

        # 年化收益率
        years = (end_date - start_date).days / 365.25
        annual_return = ((final_capital / initial_capital) ** (1/years) - 1) * 100 if years > 0 else 0

        # 计算收益率序列
        returns = []
        for i in range(1, len(equity_curve)):
            if equity_curve[i-1]['equity'] > 0:
                daily_return = (equity_curve[i]['equity'] - equity_curve[i-1]['equity']) / equity_curve[i-1]['equity']
                returns.append(daily_return)

        # 夏普比率 (假设无风险利率2%)
        if returns and np.std(returns) > 0:
            excess_returns = np.mean(returns) - 0.02/252
            sharpe_ratio = excess_returns / np.std(returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0

        # 最大回撤
        max_drawdown = 0
        peak = equity_curve[0]['equity'] if equity_curve else initial_capital
        for point in equity_curve:
            if point['equity'] > peak:
                peak = point['equity']
            drawdown = (peak - point['equity']) / peak
            max_drawdown = max(max_drawdown, drawdown)
        max_drawdown *= 100

        # 胜率
        sell_trades = [t for t in trades if t['action'] == 'sell']
        win_trades = [t for t in sell_trades if t.get('pnl_pct', 0) > 0]
        win_rate = len(win_trades) / len(sell_trades) * 100 if sell_trades else 0

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate
        }

    def optimize_parameters(
        self,
        db: Session,
        strategy: Strategy,
        start_date: str,
        end_date: str,
        param_grid: Dict,
        metric: str = "sharpe"
    ) -> Dict:
        """策略参数优化"""

        # 生成参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(itertools.product(*param_values))

        results = []

        for combo in param_combinations:
            params = dict(zip(param_names, combo))

            try:
                result = self.run_backtest(
                    db, strategy, start_date, end_date,
                    position_size=params.get('position_size', 0.2),
                    stop_loss=params.get('stop_loss', 0.07),
                    take_profit=params.get('take_profit', 0.15)
                )

                results.append({
                    'params': params,
                    'score': result.get(metric, 0),
                    'total_return': result.get('total_return', 0),
                    'sharpe_ratio': result.get('sharpe_ratio', 0),
                    'max_drawdown': result.get('max_drawdown', 0)
                })
            except Exception as e:
                continue

        # 找出最佳参数
        if not results:
            return {"error": "没有成功的回测结果"}

        if metric == "sharpe":
            best = max(results, key=lambda x: x['sharpe_ratio'])
        elif metric == "return":
            best = max(results, key=lambda x: x['total_return'])
        elif metric == "drawdown":
            best = min(results, key=lambda x: abs(x['max_drawdown']))
        else:
            best = max(results, key=lambda x: x['score'])

        return {
            "best_params": best['params'],
            "best_score": best['score'],
            "total_iterations": len(param_combinations),
            "all_results": results[:10]  # 只返回前10个结果
        }
