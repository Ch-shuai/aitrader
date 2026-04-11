'use client';

import { useEffect, useState } from 'react';
import { stockApi } from '@/app/services/api';

interface Stock {
  code: string;
  name: string;
  industry: string;
  market: string;
}

export default function StocksPage() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStocks();
  }, []);

  const loadStocks = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Loading stocks...');
      const res = await stockApi.getStocks();
      console.log('Stocks response:', res.data);
      setStocks(res.data?.items || []);
    } catch (err: any) {
      console.error('Failed to load stocks:', err);
      setError(err.message || '加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      await stockApi.syncStockList();
      await loadStocks();
    } catch (error) {
      console.error('Failed to sync:', error);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">行情中心</h1>
        <button onClick={handleSync} disabled={syncing} className="btn-primary">
          {syncing ? '同步中...' : '同步数据'}
        </button>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">股票列表</h3>
          <span className="text-sm text-gray-500">共 {stocks.length} 只</span>
        </div>
        <div className="overflow-x-auto">
          {error && (
            <div className="p-4 bg-red-50 text-red-600 rounded-lg mb-4">
              <p className="font-medium">加载失败</p>
              <p className="text-sm">{error}</p>
              <button
                onClick={loadStocks}
                className="mt-2 text-sm underline hover:no-underline"
              >
                重试
              </button>
            </div>
          )}
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : (
            <table className="table">
              <thead className="bg-gray-50">
                <tr>
                  <th>代码</th>
                  <th>名称</th>
                  <th>行业</th>
                  <th>市场</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {stocks.map((stock) => (
                  <tr key={stock.code}>
                    <td className="font-mono">{stock.code}</td>
                    <td className="font-medium">{stock.name}</td>
                    <td>{stock.industry || '-'}</td>
                    <td>
                      <span className={`badge ${stock.market === 'SH' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>
                        {stock.market}
                      </span>
                    </td>
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
