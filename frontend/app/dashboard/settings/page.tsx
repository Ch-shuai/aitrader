'use client';

import { useState } from 'react';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    apiKey: '',
    dataPath: './data',
    updateFrequency: 'daily',
    riskLevel: 'medium',
    maxPosition: 20,
    stopLoss: 7,
    takeProfit: 15,
  });

  const handleSave = () => {
    // Save settings
    alert('设置已保存');
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">设置</h1>

      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">API 配置</h3>
        </div>
        <div className="card-body space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Anthropic API Key</label>
            <input
              type="password"
              value={settings.apiKey}
              onChange={(e) => setSettings({ ...settings, apiKey: e.target.value })}
              className="input mt-1"
              placeholder="sk-..."
            />
            <p className="mt-1 text-sm text-gray-500">用于AI分析功能，仅在本地存储</p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">数据配置</h3>
        </div>
        <div className="card-body space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">数据存储路径</label>
            <input
              type="text"
              value={settings.dataPath}
              onChange={(e) => setSettings({ ...settings, dataPath: e.target.value })}
              className="input mt-1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">数据更新频率</label>
            <select
              value={settings.updateFrequency}
              onChange={(e) => setSettings({ ...settings, updateFrequency: e.target.value })}
              className="input mt-1"
            >
              <option value="realtime">实时</option>
              <option value="hourly">每小时</option>
              <option value="daily">每日</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">风控配置</h3>
        </div>
        <div className="card-body space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">最大仓位 (%)</label>
              <input
                type="number"
                value={settings.maxPosition}
                onChange={(e) => setSettings({ ...settings, maxPosition: Number(e.target.value) })}
                className="input mt-1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">止损比例 (%)</label>
              <input
                type="number"
                value={settings.stopLoss}
                onChange={(e) => setSettings({ ...settings, stopLoss: Number(e.target.value) })}
                className="input mt-1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">止盈比例 (%)</label>
              <input
                type="number"
                value={settings.takeProfit}
                onChange={(e) => setSettings({ ...settings, takeProfit: Number(e.target.value) })}
                className="input mt-1"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button onClick={handleSave} className="btn-primary">
          保存设置
        </button>
      </div>
    </div>
  );
}
