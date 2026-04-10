'use client';

import { useEffect, useState } from 'react';
import { strategyApi } from '@/app/services/api';

interface Strategy {
  id: number;
  name: string;
  code: string;
  description: string;
  type: string;
  status: string;
  is_active: boolean;
}

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [strategiesRes, categoriesRes] = await Promise.all([
        strategyApi.getStrategies(),
        strategyApi.getCategories(),
      ]);
      setStrategies(strategiesRes.data?.items || []);
      setCategories(categoriesRes.data?.categories || []);
    } catch (error) {
      console.error('Failed to load strategies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async (id: number) => {
    try {
      await strategyApi.startStrategy(id);
      await loadData();
    } catch (error) {
      console.error('Failed to start strategy:', error);
    }
  };

  const handleStop = async (id: number) => {
    try {
      await strategyApi.stopStrategy(id);
      await loadData();
    } catch (error) {
      console.error('Failed to stop strategy:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">策略中心</h1>
        <button className="btn-primary">新建策略</button>
      </div>

      {/* Strategy categories */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">14大核心策略</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {categories.map((cat) => (
              <div key={cat.id} className="border rounded-lg p-4">
                <h4 className="font-medium text-gray-900">{cat.name}</h4>
                <ul className="mt-2 space-y-1">
                  {cat.strategies.map((s: any) => (
                    <li key={s.code} className="text-sm text-gray-600">
                      • {s.name}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* My strategies */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">我的策略</h3>
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
                  <th>名称</th>
                  <th>类型</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {strategies.map((strategy) => (
                  <tr key={strategy.id}>
                    <td>
                      <div className="font-medium">{strategy.name}</div>
                      <div className="text-sm text-gray-500">{strategy.code}</div>
                    </td>
                    <td>{strategy.type}</td>
                    <td>
                      <span
                        className={`badge ${
                          strategy.status === 'running'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {strategy.status === 'running' ? '运行中' : '已停止'}
                      </span>
                    </td>
                    <td>
                      <div className="flex space-x-2">
                        {strategy.status === 'stopped' ? (
                          <button
                            onClick={() => handleStart(strategy.id)}
                            className="text-sm text-green-600 hover:text-green-700"
                          >
                            启动
                          </button>
                        ) : (
                          <button
                            onClick={() => handleStop(strategy.id)}
                            className="text-sm text-red-600 hover:text-red-700"
                          >
                            停止
                          </button>
                        )}
                      </div>
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
