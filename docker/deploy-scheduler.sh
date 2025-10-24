#!/bin/bash

# Agent2IM 定时任务调度器 - Docker 部署脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Agent2IM 定时任务调度器 - Docker 部署${NC}"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装，请先安装 Docker${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装，请先安装 Docker Compose${NC}"
    exit 1
fi

# 切换到项目根目录
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo -e "${GREEN}📂 项目目录: $PROJECT_ROOT${NC}"
echo ""

# 检查配置文件
echo -e "${YELLOW}🔍 检查配置文件...${NC}"

check_config_file() {
    local file=$1
    local required=$2
    
    if [ ! -f "$file" ]; then
        if [ "$required" = "true" ]; then
            echo -e "${RED}❌ 必需的配置文件不存在: $file${NC}"
            return 1
        else
            echo -e "${YELLOW}⚠️  可选配置文件不存在: $file${NC}"
            return 0
        fi
    else
        # 验证 JSON 格式
        if python3 -c "import json; json.load(open('$file'))" 2>/dev/null; then
            echo -e "${GREEN}✅ $file${NC}"
            return 0
        else
            echo -e "${RED}❌ 配置文件格式错误: $file${NC}"
            return 1
        fi
    fi
}

CONFIG_OK=true

# 检查必需的配置文件
check_config_file "backend/config/scheduled_tasks.json" "true" || CONFIG_OK=false
check_config_file "backend/config/labor_hour.json" "true" || CONFIG_OK=false

# 检查可选的配置文件
check_config_file "backend/config/news.json" "false"
check_config_file "backend/config/people.json" "false"
check_config_file "backend/config/task.json" "false"
check_config_file "backend/config/message.json" "false"

echo ""

if [ "$CONFIG_OK" = false ]; then
    echo -e "${RED}❌ 配置文件检查失败，请先配置必需的文件${NC}"
    echo ""
    echo -e "${YELLOW}💡 提示:${NC}"
    echo "   1. 配置 backend/config/labor_hour.json"
    echo "   2. 配置 backend/config/scheduled_tasks.json"
    echo "   3. 查看文档: docker/README_SCHEDULER.md"
    exit 1
fi

# 显示定时任务配置
echo -e "${BLUE}📅 定时任务配置:${NC}"
python3 -c "
import json
with open('backend/config/scheduled_tasks.json') as f:
    config = json.load(f)
    print(f'   时区: {config[\"timezone\"]}')
    print('   任务:')
    for task in config['tasks']:
        status = '✅' if task.get('enabled', False) else '❌'
        check_date = f' (检查{task.get(\"check_date\", \"当天\")})' if 'check_date' in task else ''
        print(f'   {status} {task[\"schedule\"]} - {task[\"name\"]}{check_date}')
" 2>/dev/null || echo "   无法解析配置文件"

echo ""

# 询问操作
echo -e "${YELLOW}请选择操作:${NC}"
echo "  1) 启动服务"
echo "  2) 停止服务"
echo "  3) 重启服务"
echo "  4) 查看日志"
echo "  5) 查看状态"
echo "  6) 重新构建并启动"
echo "  0) 退出"
echo ""
read -p "请输入选项 (默认: 1): " choice
choice=${choice:-1}

case $choice in
    1)
        echo ""
        echo -e "${GREEN}🚀 启动定时任务调度器...${NC}"
        docker-compose -f docker/docker-compose.scheduler.yml up -d
        echo ""
        echo -e "${GREEN}✅ 服务已启动${NC}"
        echo ""
        echo -e "${BLUE}💡 常用命令:${NC}"
        echo "   查看日志: docker-compose -f docker/docker-compose.scheduler.yml logs -f"
        echo "   查看状态: docker-compose -f docker/docker-compose.scheduler.yml ps"
        echo "   停止服务: docker-compose -f docker/docker-compose.scheduler.yml down"
        ;;
    2)
        echo ""
        echo -e "${YELLOW}🛑 停止服务...${NC}"
        docker-compose -f docker/docker-compose.scheduler.yml down
        echo -e "${GREEN}✅ 服务已停止${NC}"
        ;;
    3)
        echo ""
        echo -e "${YELLOW}🔄 重启服务...${NC}"
        docker-compose -f docker/docker-compose.scheduler.yml restart
        echo -e "${GREEN}✅ 服务已重启${NC}"
        ;;
    4)
        echo ""
        echo -e "${BLUE}📋 查看日志 (按 Ctrl+C 退出):${NC}"
        echo ""
        docker-compose -f docker/docker-compose.scheduler.yml logs -f
        ;;
    5)
        echo ""
        echo -e "${BLUE}📊 容器状态:${NC}"
        docker-compose -f docker/docker-compose.scheduler.yml ps
        echo ""
        echo -e "${BLUE}🏥 健康状态:${NC}"
        docker inspect --format='{{.State.Health.Status}}' agent2im-scheduler 2>/dev/null || echo "   容器未运行"
        echo ""
        echo -e "${BLUE}📈 资源使用:${NC}"
        docker stats agent2im-scheduler --no-stream 2>/dev/null || echo "   容器未运行"
        ;;
    6)
        echo ""
        echo -e "${YELLOW}🔨 重新构建并启动...${NC}"
        docker-compose -f docker/docker-compose.scheduler.yml up -d --build
        echo -e "${GREEN}✅ 服务已重新构建并启动${NC}"
        ;;
    0)
        echo "👋 再见！"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ 无效选项${NC}"
        exit 1
        ;;
esac

echo ""



