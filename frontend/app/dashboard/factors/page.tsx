'use client';

import { useEffect, useState } from 'react';
import { factorApi } from '@/app/services/api';

interface FactorCategory {
  id: string;
  name: string;
  count: number;
  description: string;
}

export default function FactorsPage() {
  const [categories, setCategories] = useState<FactorCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('');

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const res = await factorApi.getCategories();
      setCategories(res.data?.categories || []);
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">因子中心</h1>

      {/* Factor categories */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {categories.map((cat) => (
          <div
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={`card cursor-pointer transition-all ${
              selectedCategory === cat.id ? 'ring-2 ring-primary-500' : ''
            }`}
          >
            <div className="card-body">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium text-gray-900">{cat.name}</h3>
                  <p className="text-sm text-gray-500 mt-1">{cat.description}</p>
                </div>
                <span className="badge bg-primary-100 text-primary-800">{cat.count}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* IC Analysis section */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">因子IC分析</h3>
        </div>
        <div className="card-body">
          <p className="text-gray-500">选择因子查看其与未来收益的相关性分析</p>
        </div>
      </div>

      {/* Factor screening */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">因子筛选</h3>
        </div>
        <div className="card-body">
          <p className="text-gray-500">基于单因子进行股票排序筛选</p>
        </div>
      </div>
    </div>
  );
}
