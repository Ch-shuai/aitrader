'use client';

import { useEffect, useState } from 'react';
import { signalApi } from '@/app/services/api';

interface Signal {
  id: number;
  code: string;
  name: string;
  signal_type: string;
  trigger_price: number;
  confidence: number;
  reason: string;
  buy_grade: number;
  created_at: string;
}

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [highGradeSignals, setHighGradeSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    type: '',
    minGrade: 3,
  });

  useEffect(() => {
    loadSignals();
  }, [filter]);

  const loadSignals = async () => {
    try {
      setLoading(true);
      const [signalsRes, highGradeRes] = await Promise.all([
        signalApi.getSignals({ min_buy_grade: filter.minGrade, limit: 50 }),
        signalApi.getHighGradeSignals(4, 20),
      ]);
      setSignals(signalsRes.data?.items || []);
      setHighGradeSignals(highGradeRes.data?.items || []);
    } catch (error) {
      console.error('Failed to load signals:', error);
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade: number) => {
    const colors: Record<number, string> = {
      1: 'bg-red-100 text-red-800',
      2: 'bg-orange-100 text-orange-800',
      3: 'bg-yellow-100 text-yellow-800',
      4: 'bg-blue-100 text-blue-800',
      5: 'bg-green-100 text-green-800',
    };
    return colors[grade] || colors[3];
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">交易信号</h1>

      {/* High grade signals highlight */}
      <div className="card bg-gradient-to-r from-green-50 to-blue-50">
        <div className="card-header">
          <h3 className="text-lg font-medium flex items-center">
            <span className="mr-2">⭐</span>
            高等级买点信号 (4-5级)
          </h3>
          <span className="badge bg-green-100 text-green-800">
            {highGradeSignals.length} 个
          </span>
        </div>
        <div className="card-body">
          {highGradeSignals.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {highGradeSignals.map((signal) => (
                <div key={signal.id} className="bg-white rounded-lg p-4 shadow-sm">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium text-lg">{signal.name}</div>
                      <div className="text-gray-500 font-mono text-sm">{signal.code}</div>
                    </div>
                    <span className={`badge ${getGradeColor(signal.buy_grade)}`}>
                      {signal.buy_grade}级买点
                    </span>
                  </div>
                  <div className="mt-2 text-sm text-gray-600">{signal.reason}</div>
                  <div className="mt-2 flex justify-between items-center">
                    <span className="text-sm">
                      触发价: <span className="font-medium">{signal.trigger_price?.toFixed(2)}</span>
                    </span>
                    <span className="text-sm text-primary-600">
                      置信度: {(signal.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4 text-gray-500">暂无高等级买点信号</div>
          )}
        </div>
      </div>

      {/* All signals */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">全部信号</h3>
          <div className="flex items-center space-x-4">
            <select
              value={filter.minGrade}
              onChange={(e) => setFilter({ ...filter, minGrade: Number(e.target.value) })}
              className="input text-sm"
            >
              <option value={1}>全部等级</option>
              <option value={3}>3级以上</option>
              <option value={4}>4级以上</option>
            </select>
          </div>
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
                  <th>股票</th>
                  <th>类型</th>
                  <th>买点等级</th>
                  <th>触发价</th>
                  <th>置信度</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {signals.map((signal) => (
                  <tr key={signal.id}>
                    <td>
                      <div className="font-medium">{signal.name}</div>
                      <div className="text-gray-500 font-mono text-sm">{signal.code}</div>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          signal.signal_type === 'buy'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {signal.signal_type === 'buy' ? '买入' : '卖出'}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${getGradeColor(signal.buy_grade)}`}>
                        {signal.buy_grade}级
                      </span>
                    </td>
                    <td>{signal.trigger_price?.toFixed(2)}</td>
                    <td>{(signal.confidence * 100).toFixed(1)}%</td>
                    <td className="text-gray-500">{signal.created_at}</td>
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
