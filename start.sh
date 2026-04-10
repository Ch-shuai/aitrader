#!/bin/bash

# A股智能研究与交易平台 - 启动脚本

set -e

echo "========================================"
echo "  A股智能研究与交易平台 (AI Trader)"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查 Python
if ! command_exists python3; then
    echo -e "${RED}错误: 未安装 Python3${NC}"
    exit 1
fi

# 检查 Node.js
if ! command_exists node; then
    echo -e "${RED}错误: 未安装 Node.js${NC}"
    exit 1
fi

# 安装后端依赖
echo -e "${YELLOW}[1/4] 检查后端依赖...${NC}"
cd backend
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}后端依赖已就绪${NC}"

# 启动后端服务
echo -e "${YELLOW}[2/4] 启动后端服务...${NC}"
python -c "from app.core.database import init_db; init_db()" 2>/dev/null || true
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo -e "${GREEN}后端服务已启动 (PID: $BACKEND_PID)${NC}"
echo "    API地址: http://localhost:8000"
echo "    文档地址: http://localhost:8000/docs"

cd ..

# 安装前端依赖
echo ""
echo -e "${YELLOW}[3/4] 检查前端依赖...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo "安装 npm 依赖..."
    npm install
fi
echo -e "${GREEN}前端依赖已就绪${NC}"

# 启动前端服务
echo -e "${YELLOW}[4/4] 启动前端服务...${NC}"
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}前端服务已启动 (PID: $FRONTEND_PID)${NC}"
echo "    访问地址: http://localhost:3000"

cd ..

echo ""
echo "========================================"
echo -e "${GREEN}所有服务已启动!${NC}"
echo "========================================"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 捕获退出信号
trap "echo ''; echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

# 保持脚本运行
wait
