'use client';

import { useEffect, useState } from 'react';
import { backtestApi, strategyApi } from '@/app/services/api';

interface BacktestResult {
  id: number;
  strategy_id: number;
  start_date: string;
  end_date: string;
  total_return: string;
  annual_return: string;
  sharpe_ratio: number;
  max_drawdown: string;
  win_rate: string;
  trade_count: number;
}

export default function BacktestPage() {
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    strategy_id: '',
    start_date: '2023-01-01',
    end_date: '2024-01-01',
    initial_capital: 1000000,
    position_size: 0.2,
    stop_loss: 0.07,
    take_profit: 0.15,
  });
  const [running, setRunning] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [resultsRes, strategiesRes] = await Promise.all([
        backtestApi.getResults(),
        strategyApi.getStrategies(),
      ]);
      setResults(resultsRes.data?.items || []);
      setStrategies(strategiesRes.data?.items || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunBacktest = async () => {
    try {
      setRunning(true);
      await backtestApi.runBacktest({
        strategy_id: Number(form.strategy_id),
        start_date: form.start_date,
        end_date: form.end_date,
        initial_capital: form.initial_capital,
        position_size: form.position_size,
        stop_loss: form.stop_loss,
        take_profit: form.take_profit,
      });
      await loadData();
    } catch (error) {
      console.error('Failed to run backtest:', error);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">回测中心</h1>

      {/* Run backtest form */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">运行回测</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">选择策略</label>
              <select
                value={form.strategy_id}
                onChange={(e) => setForm({ ...form, strategy_id: e.target.value })}
                className="input mt-1"
              >
                <option value="">请选择</option>
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">开始日期</label>
              <input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                className="input mt-1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">结束日期</label>
              <input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                className="input mt-1"
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleRunBacktest}
              disabled={running || !form.strategy_id}
              className="btn-primary"
            >
              {running ? '运行中...' : '开始回测'}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">回测结果</h3>
        </div>
        <div className="overflow-x-auto">
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : (
            <table className="table">
              <thead className="bg-gray-50">
                <tr>
                  <th>策略</th>
                  <th>回测区间</th>
                  <th>总收益率</th>
                  <th>年化收益</th>
                  <th>夏普比率</th>
                  <th>最大回撤</th>
                  <th>胜率</th>
                  <th>交易次数</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {results.map((result) => (
                  <tr key={result.id}>
                    <td>{result.strategy_id}</td>
                    <td>
                      {result.start_date} ~ {result.end_date}
                    </td>
                    <td className={result.total_return?.startsWith('-') ? 'text-down' : 'text-up'}>
                      {result.total_return}
                    </td>
                    <td>{result.annual_return}</td>
                    <td>{result.sharpe_ratio}</td>
                    <td className="text-down">{result.max_drawdown}</td>
                    <td>{result.win_rate}</td>
                    <td>{result.trade_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
