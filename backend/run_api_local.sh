#!/bin/bash
#
# 本地运行 API 服务（用于开发调试）
#
# 使用方法:
#   chmod +x backend/run_api_local.sh
#   ./backend/run_api_local.sh
#

# 设置颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 启动本地 API 服务（开发模式）${NC}"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# 设置 PYTHONPATH
export PYTHONPATH="${PROJECT_ROOT}/backend:${PYTHONPATH}"

echo -e "${GREEN}✅ 设置环境变量${NC}"
echo "   PYTHONPATH=$PYTHONPATH"
echo ""

# 检查配置文件
echo -e "${BLUE}📋 检查配置文件...${NC}"
CONFIG_DIR="${PROJECT_ROOT}/backend/src/config"

if [ -f "${CONFIG_DIR}/labor_hour.json" ]; then
    echo -e "${GREEN}✅ labor_hour.json 存在${NC}"
else
    echo -e "${YELLOW}⚠️  labor_hour.json 不存在，请先配置${NC}"
fi

if [ -f "${CONFIG_DIR}/people.json" ]; then
    echo -e "${GREEN}✅ people.json 存在${NC}"
else
    echo -e "${YELLOW}⚠️  people.json 不存在，请先配置${NC}"
fi

echo ""

# 检查依赖
echo -e "${BLUE}📦 检查依赖...${NC}"
if python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${GREEN}✅ FastAPI 已安装${NC}"
else
    echo -e "${YELLOW}⚠️  FastAPI 未安装，正在安装...${NC}"
    pip3 install -r "${PROJECT_ROOT}/backend/requirements.txt"
fi

echo ""
echo -e "${BLUE}🎯 启动服务...${NC}"
echo -e "${GREEN}   API 服务: http://localhost:9000${NC}"
echo -e "${GREEN}   API 文档: http://localhost:9000/docs${NC}"
echo -e "${GREEN}   健康检查: http://localhost:9000/health${NC}"
echo ""
echo -e "${YELLOW}💡 提示: 按 Ctrl+C 停止服务${NC}"
echo ""

# 进入 backend 目录
cd "${PROJECT_ROOT}/backend"

# 启动服务
python3 src/api/main.py

