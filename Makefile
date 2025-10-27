.PHONY: dev

dev:
	@echo "🚀 启动 Agent2IM API 服务..."
	@echo "🔧 API 服务: http://localhost:9000"
	@echo "📚 API 文档: http://localhost:9000/docs"
	@echo "💚 健康检查: http://localhost:9000/health"
	@echo ""
	@echo "按 Ctrl+C 停止服务"
	@echo ""
	cd backend && uvicorn src.api.main:app --host 0.0.0.0 --port 9000 --reload