#!/bin/bash

# Agent2IM 生产环境启动脚本

set -e  # 遇到错误立即退出

echo "🚀 启动 Agent2IM 生产环境服务..."
echo "🔧 API服务: http://localhost:9000"
echo "📚 API文档: http://localhost:9000/docs"
echo "🌐 完全动态配置，无需配置文件！"
echo ""

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 错误处理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

# 捕获 SIGTERM 和 SIGINT 信号
trap cleanup SIGTERM SIGINT

# 显示服务信息
echo -e "${BLUE}📋 Agent2IM - 通用AI驱动的即时通讯集成平台${NC}"
echo -e "${BLUE}   支持平台: 飞书、企业微信、钉钉${NC}"
echo -e "${BLUE}   动态路由: /feishu/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}${NC}"
echo ""

# 启动API服务器
echo -e "${GREEN}⚙️  启动 Agent2IM API服务器...${NC}"
cd /app && python backend/api/main.py &
API_PID=$!

# 等待API启动
echo "等待服务启动..."
sleep 5

# 检查API是否启动成功
if ! kill -0 $API_PID 2>/dev/null; then
    echo "❌ API服务启动失败"
    exit 1
fi

echo -e "${GREEN}✅ API服务启动成功 (PID: $API_PID)${NC}"
echo ""
echo "🎉 Agent2IM 服务启动完成！"
echo "   API服务: http://localhost:9000"
echo "   健康检查: http://localhost:9000/"
echo ""
echo -e "${BLUE}💡 使用提示:${NC}"
echo "   1. 在飞书/企业微信/钉钉中配置webhook URL"
echo "   2. 格式: https://your-domain.com/feishu/webhook/{agent_id}-{auth_key}-{auth_secret}/{app_id}-{app_secret}"
echo "   3. 邀请机器人到群聊，使用 @bot 进行对话"
echo ""
echo "按 Ctrl+C 停止服务"

# 保持脚本运行，等待后台进程
wait