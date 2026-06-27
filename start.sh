#!/bin/bash
# ScoreForge 一键启动脚本 (Git Bash / Linux / Mac)
# 用法: ./start.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=5173

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null && echo "  后端已停止 (PID: $BACKEND_PID)"
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null && echo "  前端已停止 (PID: $FRONTEND_PID)"
    echo -e "${GREEN}已全部停止${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "=========================================="
echo "  ScoreForge 服务启动"
echo "=========================================="
echo ""

# 检查端口占用
if lsof -i:$BACKEND_PORT -t &>/dev/null; then
    echo -e "${RED}端口 $BACKEND_PORT 已被占用，请先停止占用进程${NC}"
    exit 1
fi
if lsof -i:$FRONTEND_PORT -t &>/dev/null; then
    echo -e "${RED}端口 $FRONTEND_PORT 已被占用，请先停止占用进程${NC}"
    exit 1
fi

# 启动后端
echo -e "${YELLOW}[1/2] 启动后端...${NC}"
cd "$BACKEND_DIR"
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
fi
uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!
echo "  后端 PID: $BACKEND_PID"

# 等待后端就绪
echo "  等待后端就绪..."
for i in $(seq 1 30); do
    if curl -s http://localhost:$BACKEND_PORT/health &>/dev/null; then
        echo -e "  ${GREEN}后端就绪 ✓${NC}"
        break
    fi
    sleep 1
done

# 启动前端
echo -e "${YELLOW}[2/2] 启动前端...${NC}"
cd "$FRONTEND_DIR"
npm run dev:h5 &
FRONTEND_PID=$!
echo "  前端 PID: $FRONTEND_PID"

# 等待前端就绪
echo "  等待前端就绪..."
for i in $(seq 1 30); do
    if curl -s http://localhost:$FRONTEND_PORT &>/dev/null; then
        echo -e "  ${GREEN}前端就绪 ✓${NC}"
        break
    fi
    sleep 1
done

echo ""
echo "=========================================="
echo -e "  ${GREEN}所有服务已启动${NC}"
echo ""
echo "  后端 API:   http://localhost:$BACKEND_PORT"
echo "  API 文档:   http://localhost:$BACKEND_PORT/docs"
echo "  前端页面:   http://localhost:$FRONTEND_PORT"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "=========================================="

wait
