'use client';

import { useState } from 'react';
import { aiApi, stockApi } from '@/app/services/api';

export default function AIPage() {
  const [stockCode, setStockCode] = useState('');
  const [analysisType, setAnalysisType] = useState('comprehensive');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [chatting, setChatting] = useState(false);

  const handleAnalyze = async () => {
    if (!stockCode) return;
    try {
      setAnalyzing(true);
      const res = await aiApi.analyzeStock(stockCode, analysisType);
      setAnalysis(res.data);
    } catch (error) {
      console.error('Failed to analyze:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleChat = async () => {
    if (!chatMessage) return;
    try {
      setChatting(true);
      setChatHistory([...chatHistory, { role: 'user', content: chatMessage }]);
      const res = await aiApi.chat(chatMessage);
      setChatHistory((prev) => [...prev, { role: 'assistant', content: res.data?.ai_response || '' }]);
      setChatMessage('');
    } catch (error) {
      console.error('Failed to chat:', error);
    } finally {
      setChatting(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">AI 服务</h1>

      {/* Stock Analysis */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">AI 股票分析</h3>
        </div>
        <div className="card-body">
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="输入股票代码"
              value={stockCode}
              onChange={(e) => setStockCode(e.target.value)}
              className="input w-48"
            />
            <select
              value={analysisType}
              onChange={(e) => setAnalysisType(e.target.value)}
              className="input w-40"
            >
              <option value="comprehensive">综合分析</option>
              <option value="technical">技术分析</option>
              <option value="fundamental">基本面分析</option>
              <option value="sentiment">情绪分析</option>
            </select>
            <button onClick={handleAnalyze} disabled={analyzing || !stockCode} className="btn-primary">
              {analyzing ? '分析中...' : '开始分析'}
            </button>
          </div>

          {analysis && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <h4 className="font-medium">
                  {analysis.name} ({analysis.code})
                </h4>
                <span className="badge bg-primary-100 text-primary-800">{analysis.analysis_type}</span>
              </div>
              {analysis.analysis?.score && (
                <div className="mb-2">
                  <span className="text-2xl font-bold">{analysis.analysis.score}</span>
                  <span className="text-gray-500 ml-2">/ 100</span>
                  <span className="ml-4 badge bg-green-100 text-green-800">{analysis.analysis.rating}</span>
                </div>
              )}
              <p className="text-gray-700">{analysis.analysis?.conclusion}</p>
            </div>
          )}
        </div>
      </div>

      {/* AI Chat */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium">AI 投资助手</h3>
        </div>
        <div className="card-body">
          <div className="h-64 overflow-y-auto border rounded-lg p-4 mb-4 bg-gray-50">
            {chatHistory.length === 0 ? (
              <div className="text-center text-gray-500 py-8">开始与AI助手对话...</div>
            ) : (
              chatHistory.map((msg, idx) => (
                <div key={idx} className={`mb-2 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                  <span
                    className={`inline-block px-3 py-2 rounded-lg ${
                      msg.role === 'user' ? 'bg-primary-100 text-primary-800' : 'bg-white border'
                    }`}
                  >
                    {msg.content}
                  </span>
                </div>
              ))
            )}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="输入您的问题..."
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleChat()}
              className="input flex-1"
            />
            <button onClick={handleChat} disabled={chatting || !chatMessage} className="btn-primary">
              {chatting ? '发送中...' : '发送'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
