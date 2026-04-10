'use client';

import { useEffect, useState } from 'react';
import { marketApi } from '@/app/services/api';

export default function MarketPage() {
  const [overview, setOverview] = useState<any>(null);
  const [sectors, setSectors] = useState<any>(null);
  const [sentiment, setSentiment] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [overviewRes, sectorsRes, sentimentRes] = await Promise.all([
        marketApi.getOverview(),
        marketApi.getSectors(20),
        marketApi.getSentiment(),
      ]);
      setOverview(overviewRes.data);
      setSectors(sectorsRes.data);
      setSentiment(sentimentRes.data);
    } catch (error) {
      console.error('Failed to load market data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEnvironmentColor = (env: string) => {
    if (env?.includes('上涨')) return 'text-red-600';
    if (env?.includes('下跌')) return 'text-green-600';
    return 'text-yellow-600';
  };

  const getSentimentColor = (index: number) => {
    if (index >= 80) return 'text-red-600';
    if (index >= 60) return 'text-orange-600';
    if (index >= 40) return 'text-yellow-600';
    if (index >= 20) return 'text-blue-600';
    return 'text-green-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">市场结构分析</h1>

      {/* Market Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="card-body">
            <div className="text-sm text-gray-500">市场环境</div>
            <div className={`text-xl font-bold ${getEnvironmentColor(overview?.environment)}`}>
              {overview?.environment || 'N/A'}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="text-sm text-gray-500">情绪指数</div>
            <div className={`text-xl font-bold ${getSentimentColor(overview?.sentiment_index || 50)}`}>
              {overview?.sentiment_index?.toFixed(1) || 'N/A'}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="text-sm text-gray-500">仓位建议</div>
            <div className="text-xl font-bold text-primary-600">
              {overview?.position_advice || 'N/A'}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="text-sm text-gray-500">热点板块</div>
            <div className="text-sm font-medium">
              {overview?.hot_sectors?.slice(0, 2).map((s: any) => s.name).join(', ') || 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {/* Sector Rotation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium">领涨板块</h3>
          </div>
          <div className="card-body">
            {sectors?.hot_sectors?.map((sector: any, idx: number) => (
              <div key={sector.name} className="flex justify-between items-center py-2 border-b last:border-0">
                <div className="flex items-center">
                  <span className="w-6 h-6 rounded-full bg-red-100 text-red-800 flex items-center justify-center text-sm font-bold mr-3">
                    {idx + 1}
                  </span>
                  <span>{sector.name}</span>
                </div>
                <span className="font-bold text-red-600">+{sector.avg_return}%</span>
              </div>
            )) || <div className="text-gray-500">暂无数据</div>}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium">领跌板块</h3>
          </div>
          <div className="card-body">
            {sectors?.cold_sectors?.map((sector: any, idx: number) => (
              <div key={sector.name} className="flex justify-between items-center py-2 border-b last:border-0">
                <div className="flex items-center">
                  <span className="w-6 h-6 rounded-full bg-green-100 text-green-800 flex items-center justify-center text-sm font-bold mr-3">
                    {idx + 1}
                  </span>
                  <span>{sector.name}</span>
                </div>
                <span className="font-bold text-green-600">{sector.avg_return}%</span>
              </div>
            )) || <div className="text-gray-500">暂无数据</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
