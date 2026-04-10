'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  TrendingUpIcon,
  BoltIcon,
  LightBulbIcon,
  NewspaperIcon,
} from '@heroicons/react/24/outline';
import { stockApi, signalApi, strategyApi, newsApi } from '@/app/services/api';

interface DashboardStats {
  totalStocks: number;
  totalFactors: number;
  activeStrategies: number;
  todaySignals: number;
  highGradeSignals: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalStocks: 0,
    totalFactors: 561,
    activeStrategies: 0,
    todaySignals: 0,
    highGradeSignals: 0,
  });
  const [recentSignals, setRecentSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      // Load stocks count
      const stocksRes = await stockApi.getStocks();
      const totalStocks = stocksRes.data?.total || 0;

      // Load strategies
      const strategiesRes = await strategyApi.getStrategies();
      const activeStrategies = strategiesRes.data?.items?.filter((s: any) => s.status === 'running').length || 0;

      // Load today's signals
      const signalsRes = await signalApi.getTodaySignals(3);
      const todaySignals = signalsRes.data?.total || 0;
      const highGradeSignals = signalsRes.data?.items?.filter((s: any) => s.buy_grade >= 4).length || 0;

      setStats({
        totalStocks,
        totalFactors: 561,
        activeStrategies,
        todaySignals,
        highGradeSignals,
      });

      setRecentSignals(signalsRes.data?.items?.slice(0, 5) || []);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
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
      {/* Stats cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="股票总数"
          value={stats.totalStocks}
          icon={TrendingUpIcon}
          color="blue"
          href="/dashboard/market"
        />
        <StatCard
          title="因子数量"
          value={stats.totalFactors}
          icon={BoltIcon}
          color="purple"
          href="/dashboard/factors"
        />
        <StatCard
          title="运行策略"
          value={stats.activeStrategies}
          icon={LightBulbIcon}
          color="yellow"
          href="/dashboard/strategies"
        />
        <StatCard
          title="今日信号"
          value={stats.todaySignals}
          subValue={`${stats.highGradeSignals}个高等级`}
          icon={NewspaperIcon}
          color="green"
          href="/dashboard/signals"
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent signals */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">最新交易信号</h3>
            <Link href="/dashboard/signals" className="text-sm text-primary-600 hover:text-primary-700">
              查看全部
            </Link>
          </div>
          <div className="card-body">
            {recentSignals.length > 0 ? (
              <table className="table">
                <thead>
                  <tr>
                    <th>股票</th>
                    <th>类型</th>
                    <th>买点等级</th>
                    <th>置信度</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {recentSignals.map((signal) => (
                    <tr key={signal.id}>
                      <td>
                        <div className="font-medium">{signal.name}</div>
                        <div className="text-gray-500">{signal.code}</div>
                      </td>
                      <td>
                        <span className={signal.signal_type === 'buy' ? 'text-up' : 'text-down'}>
                          {signal.signal_type === 'buy' ? '买入' : '卖出'}
                        </span>
                      </td>
                      <td>
                        <GradeBadge grade={signal.buy_grade} />
                      </td>
                      <td>{(signal.confidence * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="text-center py-8 text-gray-500">暂无交易信号</div>
            )}
          </div>
        </div>

        {/* Quick actions */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">快速操作</h3>
          </div>
          <div className="card-body">
            <div className="grid grid-cols-2 gap-4">
              <QuickActionCard
                title="同步股票数据"
                description="更新股票列表和行情"
                href="/dashboard/market"
                color="blue"
              />
              <QuickActionCard
                title="运行策略"
                description="执行策略生成信号"
                href="/dashboard/strategies"
                color="green"
              />
              <QuickActionCard
                title="因子分析"
                description="查看因子有效性"
                href="/dashboard/factors"
                color="purple"
              />
              <QuickActionCard
                title="回测策略"
                description="验证策略历史表现"
                href="/dashboard/backtest"
                color="orange"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  subValue,
  icon: Icon,
  color,
  href,
}: {
  title: string;
  value: number | string;
  subValue?: string;
  icon: any;
  color: 'blue' | 'purple' | 'yellow' | 'green' | 'red';
  href: string;
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    purple: 'bg-purple-50 text-purple-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
  };

  return (
    <Link href={href} className="card hover:shadow-md transition-shadow">
      <div className="card-body">
        <div className="flex items-center">
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            <Icon className="h-6 w-6" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">{title}</p>
            <p className="text-2xl font-semibold text-gray-900">{value}</p>
            {subValue && <p className="text-xs text-gray-500">{subValue}</p>}
          </div>
        </div>
      </div>
    </Link>
  );
}

function GradeBadge({ grade }: { grade: number }) {
  const colors = ['', 'bg-red-100 text-red-800', 'bg-orange-100 text-orange-800', 'bg-yellow-100 text-yellow-800', 'bg-blue-100 text-blue-800', 'bg-green-100 text-green-800'];

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors[grade] || colors[3]}`}>
      {grade}级
    </span>
  );
}

function QuickActionCard({
  title,
  description,
  href,
  color,
}: {
  title: string;
  description: string;
  href: string;
  color: 'blue' | 'green' | 'purple' | 'orange';
}) {
  const colorClasses = {
    blue: 'border-blue-200 hover:border-blue-300 hover:bg-blue-50',
    green: 'border-green-200 hover:border-green-300 hover:bg-green-50',
    purple: 'border-purple-200 hover:border-purple-300 hover:bg-purple-50',
    orange: 'border-orange-200 hover:border-orange-300 hover:bg-orange-50',
  };

  return (
    <Link
      href={href}
      className={`block p-4 border-2 border-dashed rounded-lg transition-colors ${colorClasses[color]}`}
    >
      <h4 className="font-medium text-gray-900">{title}</h4>
      <p className="mt-1 text-sm text-gray-500">{description}</p>
    </Link>
  );
}
