# A股智能研究与交易平台 (AI Trader)

基于需求文档 V6.1 开发的完整 A 股量化研究与交易平台，支持多策略、多因子、回测调优、AI 辅助决策。

## 核心功能

### 14大核心策略
- **价值投资**: F-Score、红利策略、低PB
- **成长投资**: CANSLIM、盈利增长、质量成长
- **动量策略**: 价格动量、盈利动量、行业动量
- **技术分析**: 突破策略、趋势跟踪、均值回归
- **多因子**: 质量价值、小盘成长

### 561个因子 (7大类别)
- **技术因子 (120个)**: MA、MACD、RSI、KDJ、BOLL、成交量等
- **价值因子 (85个)**: PE、PB、PS、股息率、PEG等
- **成长因子 (75个)**: 营收增长、利润增长、EPS增长等
- **质量因子 (90个)**: ROE、ROA、毛利率、周转率等
- **动量因子 (95个)**: 多期收益、Alpha/Beta、夏普比率等
- **情绪因子 (56个)**: 换手率、资金流向、北向资金等
- **宏观因子 (40个)**: 市场Beta、行业动量、风格因子等

### 买点分级系统 (1-5级)
- 5级: 极佳买点 - 多因子共振，高概率上涨
- 4级: 良好买点 - 主要因子支持
- 3级: 普通买点 - 有一定支持但需谨慎
- 2级: 观察买点 - 信号较弱
- 1级: 警惕买点 - 风险较高

### AI 辅助
- 个股智能分析 (技术/基本面/情绪/综合)
- 市场情绪分析
- 策略评估与优化建议
- 智能选股
- AI 问答助手

## 技术架构

### 后端
- **框架**: FastAPI (Python)
- **数据库**: SQLite (本地存储)
- **数据源**: AkShare (A股实时/历史数据)
- **AI 模型**: Anthropic Claude + 本地 ML 模型

### 前端
- **框架**: Next.js 14 + React 18
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **图表**: Recharts

## 快速开始

### 1. 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 启动服务

```bash
# 方式1: 使用启动脚本
./start.sh

# 方式2: 手动启动
# 终端1 - 后端
cd backend
uvicorn app.main:app --reload --port 8000

# 终端2 - 前端
cd frontend
npm run dev
```

### 3. 访问平台

- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 使用流程

### 1. 初始化数据
```
行情中心 → 同步股票数据 → 同步历史行情
```

### 2. 运行策略
```
策略中心 → 选择策略 → 启动/运行 → 生成信号
```

### 3. 查看信号
```
交易信号 → 查看高等级买点 (4-5级)
```

### 4. 回测验证
```
回测中心 → 选择策略 → 设置参数 → 运行回测
```

### 5. AI 分析
```
AI服务 → 输入股票代码 → 获取分析报告
```

## 项目结构

```
aitrader/
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/endpoints/  # API 路由
│   │   ├── core/              # 配置与数据库
│   │   ├── services/          # 业务逻辑
│   │   └── main.py            # 应用入口
│   └── requirements.txt
├── frontend/              # Next.js 前端
│   ├── app/
│   │   ├── dashboard/         # 仪表板页面
│   │   ├── services/          # API 服务
│   │   └── globals.css        # 全局样式
│   └── package.json
├── data/                  # 数据存储 (SQLite)
└── README.md
```

## API 文档

### 股票数据
- `GET /api/v1/stocks/` - 股票列表
- `GET /api/v1/stocks/{code}` - 股票详情
- `GET /api/v1/stocks/{code}/prices` - 历史行情
- `POST /api/v1/stocks/sync/list` - 同步股票列表
- `POST /api/v1/stocks/sync/prices` - 同步行情

### 因子中心
- `GET /api/v1/factors/categories` - 因子分类
- `GET /api/v1/factors/list` - 因子列表
- `POST /api/v1/factors/calculate/{code}` - 计算因子
- `GET /api/v1/factors/{code}/values` - 因子值
- `GET /api/v1/factors/screening/rank` - 因子筛选

### 策略中心
- `GET /api/v1/strategies/list` - 策略列表
- `POST /api/v1/strategies/create` - 创建策略
- `POST /api/v1/strategies/{id}/start` - 启动策略
- `POST /api/v1/strategies/{id}/run` - 运行策略

### 交易信号
- `GET /api/v1/signals/list` - 信号列表
- `GET /api/v1/signals/today` - 今日信号
- `GET /api/v1/signals/high-grade` - 高等级信号

### 回测中心
- `POST /api/v1/backtest/run` - 运行回测
- `GET /api/v1/backtest/results` - 回测结果
- `POST /api/v1/backtest/optimize/{id}` - 参数优化

### AI 服务
- `POST /api/v1/ai/analyze-stock` - 股票分析
- `POST /api/v1/ai/analyze-market` - 市场分析
- `POST /api/v1/ai/chat` - AI 对话

## 配置说明

### 环境变量 (.env)
```env
# AI 配置
ANTHROPIC_API_KEY=your_api_key

# 数据库
DATABASE_URL=sqlite:///data/aitrader.db

# 数据源
TUSHARE_TOKEN=your_token
```

### 风控参数
- 单票最大仓位: 20%
- 止损线: 7%
- 止盈线: 15%
- 最大回撤: 15%

## 开发计划

- [x] 项目架构搭建
- [x] 数据库模型设计
- [x] 后端 API 开发
- [x] 前端界面开发
- [ ] 数据自动更新
- [ ] 更多策略实现
- [ ] ML 模型训练
- [ ] 实盘交易接口

## 许可证

MIT
