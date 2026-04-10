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

### 机器学习预测
- XGBoost 预测模型
- 自动模型训练
- 涨跌概率预测
- 批量模型训练

### 市场结构分析
- 市场环境评估 (强势/震荡/弱势)
- 板块轮动检测
- 综合情绪指数
- 个股风险预警

### 定时任务
- 每日收盘后自动同步数据
- 自动计算因子
- 定时同步新闻
- 过期数据清理

## 技术架构

### 后端
- **框架**: FastAPI (Python)
- **数据库**: SQLite (本地存储)
- **数据源**: AkShare (A股实时/历史数据)
- **AI 模型**: Anthropic Claude + XGBoost + 本地 ML
- **定时任务**: APScheduler

### 前端
- **框架**: Next.js 14 + React 18
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **图表**: Recharts

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/Ch-shuai/aitrader.git
cd aitrader
```

### 2. 启动服务

```bash
# 使用启动脚本（推荐）
./start.sh

# 或手动启动
# 后端
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

### 3. 访问平台

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 使用流程

### 首次使用

1. **初始化数据**
   ```
   访问: http://localhost:3000/dashboard
   进入 "数据同步" 页面
   点击 "初始化数据" 按钮
   ```

2. **查看市场环境**
   ```
   进入 "市场结构" 页面
   查看当前市场环境和情绪指数
   ```

### 日常使用

1. **运行策略**
   ```
   策略中心 → 选择策略 → 启动/运行 → 生成信号
   ```

2. **查看信号**
   ```
   交易信号 → 查看高等级买点 (4-5级)
   ```

3. **AI 分析**
   ```
   AI服务 → 输入股票代码 → 获取分析报告
   或 ML预测 → 训练模型 → 查看预测结果
   ```

4. **回测验证**
   ```
   回测中心 → 选择策略 → 设置参数 → 运行回测
   ```

## API 文档

### 主要 API 端点

| 端点 | 功能 |
|------|------|
| `GET /api/v1/stocks/` | 股票列表 |
| `GET /api/v1/stocks/{code}/prices` | 历史行情 |
| `GET /api/v1/factors/categories` | 因子分类 |
| `POST /api/v1/factors/calculate/{code}` | 计算因子 |
| `GET /api/v1/strategies/list` | 策略列表 |
| `POST /api/v1/strategies/{id}/run` | 运行策略 |
| `GET /api/v1/signals/today` | 今日信号 |
| `GET /api/v1/signals/high-grade` | 高等级信号 |
| `POST /api/v1/backtest/run` | 运行回测 |
| `POST /api/v1/ml/train/{code}` | 训练ML模型 |
| `GET /api/v1/ml/predict/{code}` | 预测走势 |
| `GET /api/v1/market/environment` | 市场环境 |
| `GET /api/v1/market/sentiment` | 市场情绪 |
| `POST /api/v1/sync/initialize` | 初始化数据 |
| `GET /api/v1/scheduler/jobs` | 定时任务 |

完整 API 文档: http://localhost:8000/docs

## 项目结构

```
aitrader/
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/endpoints/  # API 路由
│   │   ├── core/              # 配置与数据库
│   │   ├── services/          # 业务逻辑
│   │   │   ├── data_service.py      # 数据同步
│   │   │   ├── factor_service.py    # 因子计算
│   │   │   ├── strategy_service.py  # 策略执行
│   │   │   ├── backtest_service.py  # 回测引擎
│   │   │   ├── ai_service.py        # AI分析
│   │   │   ├── ml_service.py        # 机器学习
│   │   │   ├── market_service.py    # 市场结构
│   │   │   ├── scheduler_service.py # 定时任务
│   │   │   └── sync_service.py      # 数据同步
│   │   └── main.py            # 应用入口
│   └── requirements.txt
├── frontend/              # Next.js 前端
│   ├── app/
│   │   ├── dashboard/         # 仪表板页面
│   │   ├── services/          # API 服务
│   │   └── globals.css        # 全局样式
│   └── package.json
├── data/                  # 数据存储 (SQLite)
├── test_features.py       # 功能测试脚本
└── README.md
```

## 配置说明

### 环境变量 (.env)
```env
# AI 配置 (可选)
ANTHROPIC_API_KEY=sk-ant-api03-your-api-key

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=true

# 风控参数
MAX_POSITION_PCT=0.2
STOP_LOSS_PCT=0.07
TAKE_PROFIT_PCT=0.15
```

### 定时任务配置

默认定时任务:
- **15:30** - 同步股票列表
- **15:45** - 同步日线行情
- **16:00** - 计算因子
- **每小时** - 同步新闻
- **每周一 9:00** - 清理过期数据

## 功能测试

```bash
cd /Users/ch_shuai/Desktop/cc_home/aitrader
source backend/venv/bin/activate
python test_features.py
```

## 开发路线图

- [x] 项目架构搭建
- [x] 数据库模型设计
- [x] 后端 API 开发
- [x] 前端界面开发
- [x] 14大核心策略
- [x] 561因子体系
- [x] 定时任务调度
- [x] 数据同步自动化
- [x] F-Score财务数据
- [x] XGBoost ML模型
- [x] 市场结构分析
- [ ] 更多策略优化
- [ ] 实盘交易接口

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request!

## 联系方式

GitHub: https://github.com/Ch-shuai/aitrader
