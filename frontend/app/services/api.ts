import axios from 'axios';

// 使用相对路径，通过Next.js rewrite代理到后端
// 避免CORS问题和307重定向问题
const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Stock API
export const stockApi = {
  getStocks: (params?: { industry?: string; market?: string }) =>
    api.get('/stocks/', { params }),
  getStockDetail: (code: string) => api.get(`/stocks/${code}`),
  getStockPrices: (code: string, days?: number) =>
    api.get(`/stocks/${code}/prices`, { params: { days } }),
  syncStockList: () => api.post('/stocks/sync/list'),
  syncPrices: (code?: string) => api.post('/stocks/sync/prices', { code }),
};

// Factor API
export const factorApi = {
  getCategories: () => api.get('/factors/categories'),
  getFactors: (params?: { category?: string; search?: string }) =>
    api.get('/factors/list', { params }),
  calculateFactors: (code: string, data?: any) =>
    api.post(`/factors/calculate/${code}`, data),
  getFactorValues: (code: string, params?: any) =>
    api.get(`/factors/${code}/values`, { params }),
  getLatestFactors: (code: string, category?: string) =>
    api.get(`/factors/${code}/latest`, { params: { category } }),
  screenByFactor: (params: {
    factor_name: string;
    order?: string;
    date?: string;
    industry?: string;
    limit?: number;
  }) => api.get('/factors/screening/rank', { params }),
};

// Strategy API
export const strategyApi = {
  getCategories: () => api.get('/strategies/categories'),
  getStrategies: (params?: { category?: string; status?: string }) =>
    api.get('/strategies/list', { params }),
  getStrategy: (id: number) => api.get(`/strategies/${id}`),
  createStrategy: (data: any) => api.post('/strategies/create', data),
  updateStrategy: (id: number, data: any) => api.put(`/strategies/${id}`, data),
  startStrategy: (id: number) => api.post(`/strategies/${id}/start`),
  stopStrategy: (id: number) => api.post(`/strategies/${id}/stop`),
  runStrategy: (id: number, date?: string) =>
    api.post(`/strategies/${id}/run`, { date }),
  deleteStrategy: (id: number) => api.delete(`/strategies/${id}`),
  getPresetDetail: (code: string) => api.get(`/strategies/preset/${code}`),
};

// Signal API
export const signalApi = {
  getSignals: (params?: {
    code?: string;
    strategy_id?: number;
    signal_type?: string;
    status?: string;
    min_buy_grade?: number;
    limit?: number;
  }) => api.get('/signals/list', { params }),
  getTodaySignals: (min_grade?: number) =>
    api.get('/signals/today', { params: { min_buy_grade: min_grade } }),
  getHighGradeSignals: (min_grade?: number, limit?: number) =>
    api.get('/signals/high-grade', { params: { min_grade, limit } }),
  getSignalDetail: (id: number) => api.get(`/signals/${id}`),
  confirmSignal: (id: number) => api.post(`/signals/${id}/confirm`),
  executeSignal: (id: number) => api.post(`/signals/${id}/execute`),
  cancelSignal: (id: number, reason?: string) =>
    api.post(`/signals/${id}/cancel`, { reason }),
};

// Backtest API
export const backtestApi = {
  runBacktest: (data: {
    strategy_id: number;
    start_date: string;
    end_date: string;
    initial_capital?: number;
    position_size?: number;
    stop_loss?: number;
    take_profit?: number;
  }) => api.post('/backtest/run', data),
  getResults: (params?: { strategy_id?: number; limit?: number }) =>
    api.get('/backtest/results', { params }),
  getResultDetail: (id: number) => api.get(`/backtest/${id}`),
  getTrades: (id: number) => api.get(`/backtest/${id}/trades`),
  getEquityCurve: (id: number) => api.get(`/backtest/${id}/equity-curve`),
  optimizeStrategy: (strategy_id: number, data: any) =>
    api.post(`/backtest/optimize/${strategy_id}`, data),
  deleteResult: (id: number) => api.delete(`/backtest/${id}`),
};

// News API
export const newsApi = {
  getNews: (params?: {
    category?: string;
    source?: string;
    keyword?: string;
    sentiment?: string;
    limit?: number;
  }) => api.get('/news/list', { params }),
  getLatest: (hours?: number, limit?: number) =>
    api.get('/news/latest', { params: { hours, limit } }),
  getDetail: (id: number) => api.get(`/news/${id}`),
  getSources: () => api.get('/news/sources/list'),
  getCategories: () => api.get('/news/categories/list'),
  getSentimentStats: (days?: number) =>
    api.get('/news/sentiment/stats', { params: { days } }),
  syncNews: (keyword?: string, limit?: number) =>
    api.post('/news/sync', { keyword, limit }),
  search: (q: string, limit?: number) =>
    api.get('/news/search', { params: { q, limit } }),
};

// AI API
export const aiApi = {
  analyzeStock: (code: string, analysis_type?: string) =>
    api.post('/ai/analyze-stock', { code, analysis_type }),
  analyzeMarket: (analysis_type?: string) =>
    api.post('/ai/analyze-market', { analysis_type }),
  reviewStrategy: (strategy_id: number, review_type?: string) =>
    api.post('/ai/strategy-review', { strategy_id, review_type }),
  generateStrategy: (
    market_condition: string,
    risk_preference?: string,
    investment_style?: string
  ) =>
    api.post('/ai/generate-strategy', {
      market_condition,
      risk_preference,
      investment_style,
    }),
  analyzeSentiment: (text?: string, news_id?: number) =>
    api.post('/ai/sentiment-analysis', { text, news_id }),
  stockSelection: (criteria: string, max_results?: number) =>
    api.post('/ai/stock-selection', { criteria, max_results }),
  chat: (message: string, context?: any) =>
    api.post('/ai/chat', { message, context }),
  generateDailyReport: (date?: string, report_type?: string) =>
    api.post('/ai/report/daily', { date, report_type }),
  analyzeRisk: (code?: string, portfolio?: string[]) =>
    api.post('/ai/risk-warning', { code, portfolio }),
  getModelsStatus: () => api.get('/ai/models/status'),
};

// Scheduler API
export const schedulerApi = {
  getJobs: () => api.get('/scheduler/jobs'),
  start: () => api.post('/scheduler/start'),
  stop: () => api.post('/scheduler/stop'),
  getStatus: () => api.get('/scheduler/status'),
  runJob: (jobId: string) => api.post(`/scheduler/run/${jobId}`),
};

// Sync API
export const syncApi = {
  initialize: () => api.post('/sync/initialize'),
  dailyUpdate: () => api.post('/sync/daily-update'),
  getStatus: () => api.get('/sync/status'),
  syncStocks: () => api.post('/sync/stocks'),
  syncPrices: (code?: string) => api.post('/sync/prices', { code }),
  calculateFactors: (code?: string) => api.post('/sync/factors', { code }),
};

// ML API
export const mlApi = {
  trainModel: (code: string, modelType?: string) =>
    api.post(`/ml/train/${code}`, null, { params: { model_type: modelType } }),
  batchTrain: (maxStocks?: number) =>
    api.post('/ml/batch-train', null, { params: { max_stocks: maxStocks } }),
  predict: (code: string, daysAhead?: number) =>
    api.get(`/ml/predict/${code}`, { params: { days_ahead: daysAhead } }),
  getPerformance: (code?: string) =>
    api.get('/ml/performance', { params: { code } }),
  getStatus: () => api.get('/ml/status'),
};

// Market API
export const marketApi = {
  getEnvironment: () => api.get('/market/environment'),
  getSectors: (days?: number) => api.get('/market/sectors', { params: { days } }),
  getSentiment: () => api.get('/market/sentiment'),
  getRiskWarning: (code: string) => api.get(`/market/risk-warning/${code}`),
  getOverview: () => api.get('/market/overview'),
};

export default api;
