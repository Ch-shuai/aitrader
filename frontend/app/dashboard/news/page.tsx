'use client';

import { useEffect, useState } from 'react';
import { newsApi } from '@/app/services/api';

interface NewsItem {
  id: number;
  title: string;
  content: string;
  source: string;
  category: string;
  sentiment: string;
  publish_time: string;
}

export default function NewsPage() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [filter, setFilter] = useState({
    category: '',
    sentiment: '',
  });

  useEffect(() => {
    loadData();
  }, [filter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [newsRes, categoriesRes, sourcesRes] = await Promise.all([
        newsApi.getNews(filter),
        newsApi.getCategories(),
        newsApi.getSources(),
      ]);
      setNews(newsRes.data?.items || []);
      setCategories(categoriesRes.data?.categories || []);
      setSources(sourcesRes.data?.sources || []);
    } catch (error) {
      console.error('Failed to load news:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      setSyncing(true);
      await newsApi.syncNews();
      await loadData();
    } catch (error) {
      console.error('Failed to sync:', error);
    } finally {
      setSyncing(false);
    }
  };

  const getSentimentColor = (sentiment: string) => {
    const colors: Record<string, string> = {
      positive: 'bg-green-100 text-green-800',
      negative: 'bg-red-100 text-red-800',
      neutral: 'bg-gray-100 text-gray-800',
    };
    return colors[sentiment] || colors.neutral;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">资讯中心</h1>
        <button onClick={handleSync} disabled={syncing} className="btn-primary">
          {syncing ? '同步中...' : '同步新闻'}
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="card-body flex gap-4">
          <select
            value={filter.category}
            onChange={(e) => setFilter({ ...filter, category: e.target.value })}
            className="input w-40"
          >
            <option value="">全部分类</option>
            {categories.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name} ({c.count})
              </option>
            ))}
          </select>
          <select
            value={filter.sentiment}
            onChange={(e) => setFilter({ ...filter, sentiment: e.target.value })}
            className="input w-32"
          >
            <option value="">全部情感</option>
            <option value="positive">正面</option>
            <option value="neutral">中性</option>
            <option value="negative">负面</option>
          </select>
        </div>
      </div>

      {/* News list */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          news.map((item) => (
            <div key={item.id} className="card hover:shadow-md transition-shadow">
              <div className="card-body">
                <div className="flex justify-between items-start">
                  <h3 className="font-medium text-lg">{item.title}</h3>
                  {item.sentiment && (
                    <span className={`badge ${getSentimentColor(item.sentiment)}`}>
                      {item.sentiment === 'positive' ? '正面' : item.sentiment === 'negative' ? '负面' : '中性'}
                    </span>
                  )}
                </div>
                <p className="mt-2 text-gray-600 text-sm">{item.content}</p>
                <div className="mt-3 flex items-center text-sm text-gray-500">
                  <span className="mr-4">来源: {item.source}</span>
                  <span className="mr-4">分类: {item.category}</span>
                  <span>{item.publish_time}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
