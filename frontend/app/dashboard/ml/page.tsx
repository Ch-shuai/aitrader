'use client';

import { useEffect, useState } from 'react';
import { mlApi } from '@/app/services/api';

export default function MLPage() {
  const [stockCode, setStockCode] = useState('');
  const [training, setTraining] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [trainResult, setTrainResult] = useState<any>(null);
  const [predictResult, setPredictResult] = useState<any>(null);
  const [mlStatus, setMlStatus] = useState<any>(null);
  const [batchTraining, setBatchTraining] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const res = await mlApi.getStatus();
      setMlStatus(res.data);
    } catch (error) {
      console.error('Failed to load ML status:', error);
    }
  };

  const handleTrain = async () => {
    if (!stockCode) return;
    try {
      setTraining(true);
      const res = await mlApi.trainModel(stockCode, 'xgboost');
      setTrainResult(res.data);
    } catch (error) {
      console.error('Failed to train:', error);
    } finally {
      setTraining(false);
    }
  };

  const handlePredict = async () => {
    if (!stockCode) return;
    try {
      setPredicting(true);
      const res = await mlApi.predict(stockCode, 5);
      setPredictResult(res.data);
    } catch (error) {
      console.error('Failed to predict:', error);
    } finally {
      setPredicting(false);
    }
  };

  const handleBatchTrain = async () => {
    try {
      setBatchTraining(true);
      const res = await mlApi.batchTrain(50);
      alert(`批量训练已启动: ${res.data?.total} 只股票`);
    } catch (error) {
      console.error('Failed to batch train:', error);
    } finally {
      setBatchTraining(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">机器学习预测</h1>
        <div className="flex items-center space-x-4">
          <span className={`badge ${mlStatus?.ml_available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            {mlStatus?.ml_available ? 'ML服务正常' : 'ML服务不可用'}
          </span>
          <button onClick={handleBatchTrain} disabled={batchTraining} className="btn-primary">
            {batchTraining ? '训练中...' : '批量训练'}
          </button>
        </div>
      </div>

      {/* ML Status */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">服务状态</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-500">已训练模型</div>
              <div className="text-2xl font-bold">{mlStatus?.trained_models || 0}</div>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-500">支持模型</div>
              <div className="text-lg font-medium">
                {mlStatus?.supported_models?.join(', ') || 'N/A'}
              </div>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-500">状态</div>
              <div className={`text-lg font-medium ${mlStatus?.ml_available ? 'text-green-600' : 'text-red-600'}`}>
                {mlStatus?.ml_available ? '可用' : '不可用'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Train & Predict */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Train Model */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium">训练模型</h3>
          </div>
          <div className="card-body space-y-4">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="输入股票代码 (如: 000001)"
                value={stockCode}
                onChange={(e) => setStockCode(e.target.value)}
                className="input flex-1"
              />
              <button
                onClick={handleTrain}
                disabled={training || !stockCode}
                className="btn-primary"
              >
                {training ? '训练中...' : '训练'}
              </button>
            </div>

            {trainResult && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium mb-2">训练结果: {trainResult.code}</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>准确率: <span className="font-bold">{(trainResult.accuracy * 100).toFixed(2)}%</span></div>
                  <div>精确率: <span className="font-bold">{(trainResult.precision * 100).toFixed(2)}%</span></div>
                  <div>召回率: <span className="font-bold">{(trainResult.recall * 100).toFixed(2)}%</span></div>
                  <div>训练样本: {trainResult.train_samples}</div>
                </div>
                {trainResult.feature_importance && (
                  <div className="mt-2">
                    <div className="text-sm text-gray-600">重要特征:</div>
                    <div className="text-sm">
                      {Object.entries(trainResult.feature_importance)
                        .slice(0, 3)
                        .map(([k, v]) => `${k}: ${(v as number).toFixed(3)}`)
                        .join(', ')}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Predict */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium">走势预测</h3>
          </div>
          <div className="card-body space-y-4">
            <div className="flex gap-4">
              <input
                type="text"
                placeholder="输入股票代码"
                value={stockCode}
                onChange={(e) => setStockCode(e.target.value)}
                className="input flex-1"
              />
              <button
                onClick={handlePredict}
                disabled={predicting || !stockCode}
                className="btn-primary"
              >
                {predicting ? '预测中...' : '预测'}
              </button>
            </div>

            {predictResult && (
              <div className={`p-4 rounded-lg ${predictResult.prediction === '上涨' ? 'bg-red-50' : 'bg-green-50'}`}>
                <h4 className="font-medium mb-2">预测结果: {predictResult.code}</h4>
                <div className="text-3xl font-bold mb-2">
                  {predictResult.prediction}
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>置信度: <span className="font-bold">{(predictResult.confidence * 100).toFixed(1)}%</span></div>
                  <div>上涨概率: <span className="font-bold">{(predictResult.up_probability * 100).toFixed(1)}%</span></div>
                  <div>趋势强度: <span className="font-bold">{(predictResult.trend_strength * 100).toFixed(1)}%</span></div>
                  <div>模型准确率: <span className="font-bold">{(predictResult.model_accuracy * 100).toFixed(1)}%</span></div>
                </div>
                {predictResult.factors && (
                  <div className="mt-2 text-sm">
                    <div>近期收益: {predictResult.factors.recent_return}%</div>
                    <div>RSI: {predictResult.factors.rsi}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
