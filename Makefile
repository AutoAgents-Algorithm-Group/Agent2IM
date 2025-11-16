.PHONY: dev app-build app-up app-restart app-logs app-down scheduler-build scheduler-up scheduler-restart scheduler-logs scheduler-down docker-up docker-down docker-logs docker-ps

# 本地开发环境
dev:
	@echo "🚀 启动 Agent2IM API 服务（开发模式）..."
	@echo "🔧 API 服务: http://localhost:9000"
	@echo "📚 API 文档: http://localhost:9000/docs"
	@echo "💚 健康检查: http://localhost:9000/health"
	@echo ""
	@echo "按 Ctrl+C 停止服务"
	@echo ""
	cd backend && uvicorn src.api.main:app --host 0.0.0.0 --port 9000 --reload

# ============================================
# 应用服务管理（独立部署）
# ============================================

app-build:
	@echo "🔨 构建应用服务镜像..."
	cd docker && docker compose build app

app-up:
	@echo "🚀 启动应用服务..."
	cd docker && docker compose up -d app
	@echo "✅ 应用服务已启动"
	@echo "🔧 API 服务: http://localhost:9000"
	@echo "📚 API 文档: http://localhost:9000/docs"
	@echo "💚 健康检查: http://localhost:9000/health"

app-restart:
	@echo "🔄 重启应用服务..."
	cd docker && docker compose restart app
	@echo "✅ 应用服务已重启"

app-logs:
	@echo "📋 查看应用服务日志（按 Ctrl+C 退出）..."
	cd docker && docker compose logs -f app

app-down:
	@echo "🛑 停止应用服务..."
	cd docker && docker compose stop app
	@echo "✅ 应用服务已停止"

app-rebuild:
	@echo "🔄 重新构建并部署应用服务..."
	cd docker && docker compose build app && docker compose up -d app
	@echo "✅ 应用服务已重新部署"
	@make app-logs

# ============================================
# Scheduler 服务管理（独立部署）
# ============================================

scheduler-build:
	@echo "🔨 构建 Scheduler 服务镜像..."
	cd docker && docker compose build scheduler

scheduler-up:
	@echo "🚀 启动 Scheduler 服务..."
	cd docker && docker compose up -d scheduler
	@echo "✅ Scheduler 服务已启动"

scheduler-restart:
	@echo "🔄 重启 Scheduler 服务..."
	cd docker && docker compose restart scheduler
	@echo "✅ Scheduler 服务已重启"

scheduler-logs:
	@echo "📋 查看 Scheduler 服务日志（按 Ctrl+C 退出）..."
	cd docker && docker compose logs -f scheduler

scheduler-down:
	@echo "🛑 停止 Scheduler 服务..."
	cd docker && docker compose stop scheduler
	@echo "✅ Scheduler 服务已停止"

scheduler-rebuild:
	@echo "🔄 重新构建并部署 Scheduler 服务..."
	cd docker && docker compose build scheduler && docker compose up -d scheduler
	@echo "✅ Scheduler 服务已重新部署"
	@make scheduler-logs

# ============================================
# Docker 综合管理命令
# ============================================

docker-up:
	@echo "🚀 启动所有服务..."
	cd docker && docker compose up -d
	@echo "✅ 所有服务已启动"
	@make docker-ps

docker-down:
	@echo "🛑 停止所有服务..."
	cd docker && docker compose down
	@echo "✅ 所有服务已停止"

docker-logs:
	@echo "📋 查看所有服务日志（按 Ctrl+C 退出）..."
	cd docker && docker compose logs -f

docker-ps:
	@echo "📊 容器状态："
	cd docker && docker compose ps

# ============================================
# 帮助信息
# ============================================

help:
	@echo "Agent2IM 部署命令帮助"
	@echo ""
	@echo "本地开发："
	@echo "  make dev              - 启动应用服务（开发模式，支持热重载）"
	@echo ""
	@echo "应用服务管理（独立部署）："
	@echo "  make app-build        - 构建应用镜像"
	@echo "  make app-up           - 启动应用服务"
	@echo "  make app-restart      - 重启应用服务"
	@echo "  make app-rebuild      - 重新构建并部署应用"
	@echo "  make app-logs         - 查看应用日志"
	@echo "  make app-down         - 停止应用服务"
	@echo ""
	@echo "Scheduler 服务管理（独立部署）："
	@echo "  make scheduler-build  - 构建 Scheduler 镜像"
	@echo "  make scheduler-up     - 启动 Scheduler 服务"
	@echo "  make scheduler-restart- 重启 Scheduler 服务"
	@echo "  make scheduler-rebuild- 重新构建并部署 Scheduler"
	@echo "  make scheduler-logs   - 查看 Scheduler 日志"
	@echo "  make scheduler-down   - 停止 Scheduler 服务"
	@echo ""
	@echo "综合管理："
	@echo "  make docker-up        - 启动所有服务"
	@echo "  make docker-down      - 停止所有服务"
	@echo "  make docker-logs      - 查看所有服务日志"
	@echo "  make docker-ps        - 查看容器状态"
	@echo ""
	@echo "示例场景："
	@echo "  1️⃣  只修改了应用代码，重新部署应用："
	@echo "     make app-rebuild"
	@echo ""
	@echo "  2️⃣  只修改了 Scheduler 代码，重新部署 Scheduler："
	@echo "     make scheduler-rebuild"
	@echo ""
	@echo "  3️⃣  首次部署所有服务："
	@echo "     make docker-up"