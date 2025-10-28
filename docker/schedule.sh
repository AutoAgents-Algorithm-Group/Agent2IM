#!/bin/bash
################################################################################
# 定时任务调度器启动脚本
# 
# 功能：
#   - 启动统一定时任务调度器
#   - 包含新闻推送和工时检查任务
#   - 用于 Docker 容器中运行
#
# 使用方法：
#   ./schedule.sh
################################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 分隔线
separator() {
    echo "================================================================================"
}

# 主函数
main() {
    separator
    log_info "🚀 启动统一定时任务调度器"
    separator
    echo ""
    
    # 检查 Python 环境
    if ! command -v python &> /dev/null; then
        log_error "❌ Python 未安装"
        exit 1
    fi
    
    log_info "Python 版本: $(python --version)"
    
    # 设置环境变量
    export PYTHONPATH=/app/backend
    export PYTHONUNBUFFERED=1
    export TZ=Asia/Shanghai
    
    log_info "工作目录: $(pwd)"
    log_info "PYTHONPATH: $PYTHONPATH"
    log_info "时区: $TZ"
    echo ""
    
    # 检查配置文件
    CONFIG_FILES=(
        "/app/backend/src/config/labor_hour.yaml"
        "/app/backend/src/config/approval.yaml"
        "/app/backend/src/config/news.yaml"
    )
    
    log_info "检查配置文件..."
    for config in "${CONFIG_FILES[@]}"; do
        if [ -f "$config" ]; then
            log_success "✓ $config"
        else
            log_warning "⚠ $config 不存在（可能为可选配置）"
        fi
    done
    echo ""
    
    # 启动调度器
    separator
    log_info "正在启动 Python 调度器..."
    separator
    echo ""
    
    # 直接运行 unified_scheduler.py
    cd /app/backend
    python -u src/utils/schedule/unified_scheduler.py
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_success "👋 调度器正常退出"
    else
        log_error "❌ 调度器异常退出 (Exit Code: $EXIT_CODE)"
        exit $EXIT_CODE
    fi
}

# 捕获信号
trap 'log_warning "收到退出信号"; exit 0' SIGTERM SIGINT

# 执行主函数
main

exit 0

