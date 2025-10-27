.PHONY: help run stop restart logs status test clean install check docker-up docker-down docker-restart docker-logs config

# 默认目标
.DEFAULT_GOAL := help

# 项目路径
PROJECT_ROOT := $(shell pwd)
BACKEND_DIR := $(PROJECT_ROOT)/backend
DOCKER_COMPOSE := docker compose -f docker/docker-compose.yml

# Python 环境
PYTHON := $(shell which python3 || which python)
CONDA_ENV := $(CONDA_DEFAULT_ENV)
export PYTHONPATH := $(BACKEND_DIR):$(PYTHONPATH)

# 颜色输出
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

##@ 帮助信息

help: ## 显示帮助信息
	@echo ""
	@echo "$(BLUE)🚀 Agent2IM - HR 小助手$(NC)"
	@echo ""
	@echo "$(GREEN)可用命令:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ 本地开发

run: ## 启动本地 API 服务（开发模式）
	@echo "$(BLUE)🚀 启动本地 API 服务...$(NC)"
	@if [ -n "$(CONDA_ENV)" ]; then \
		echo "$(GREEN)✅ Conda 环境: $(CONDA_ENV)$(NC)"; \
	fi
	@echo "$(GREEN)✅ Python: $(PYTHON)$(NC)"
	@echo "$(GREEN)✅ PYTHONPATH=$(PYTHONPATH)$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) src/api/main.py

install: ## 安装 Python 依赖
	@echo "$(BLUE)📦 安装依赖...$(NC)"
	@if [ -n "$(CONDA_ENV)" ]; then \
		echo "$(GREEN)使用 Conda 环境: $(CONDA_ENV)$(NC)"; \
		pip install -r $(BACKEND_DIR)/requirements.txt; \
	else \
		pip3 install -r $(BACKEND_DIR)/requirements.txt; \
	fi
	@echo "$(GREEN)✅ 依赖安装完成$(NC)"

check: ## 检查配置文件和依赖
	@echo "$(BLUE)🔍 检查配置...$(NC)"
	@echo ""
	@echo "$(BLUE)📋 配置文件:$(NC)"
	@if [ -f "$(BACKEND_DIR)/src/config/labor_hour.json" ]; then \
		echo "  $(GREEN)✅ labor_hour.json$(NC)"; \
	else \
		echo "  $(RED)❌ labor_hour.json 不存在$(NC)"; \
	fi
	@if [ -f "$(BACKEND_DIR)/src/config/people.json" ]; then \
		echo "  $(GREEN)✅ people.json$(NC)"; \
	else \
		echo "  $(RED)❌ people.json 不存在$(NC)"; \
	fi
	@if [ -f "$(BACKEND_DIR)/src/config/scheduled_tasks.json" ]; then \
		echo "  $(GREEN)✅ scheduled_tasks.json$(NC)"; \
	else \
		echo "  $(RED)❌ scheduled_tasks.json 不存在$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)🐍 Python 环境:$(NC)"
	@if [ -n "$(CONDA_ENV)" ]; then \
		echo "  $(GREEN)✅ Conda 环境: $(CONDA_ENV)$(NC)"; \
	else \
		echo "  $(YELLOW)⚠️  未检测到 Conda 环境$(NC)"; \
	fi
	@echo "  Python: $(PYTHON)"
	@echo ""
	@echo "$(BLUE)📦 Python 依赖:$(NC)"
	@$(PYTHON) -c "import fastapi" 2>/dev/null && echo "  $(GREEN)✅ FastAPI$(NC)" || echo "  $(RED)❌ FastAPI 未安装$(NC)"
	@$(PYTHON) -c "import uvicorn" 2>/dev/null && echo "  $(GREEN)✅ Uvicorn$(NC)" || echo "  $(RED)❌ Uvicorn 未安装$(NC)"
	@$(PYTHON) -c "import requests" 2>/dev/null && echo "  $(GREEN)✅ Requests$(NC)" || echo "  $(RED)❌ Requests 未安装$(NC)"
	@$(PYTHON) -c "import apscheduler" 2>/dev/null && echo "  $(GREEN)✅ APScheduler$(NC)" || echo "  $(RED)❌ APScheduler 未安装$(NC)"
	@echo ""

##@ Docker 部署

docker-up: ## 启动 Docker 服务
	@echo "$(BLUE)🐳 启动 Docker 服务...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Docker 服务已启动$(NC)"
	@echo ""
	@$(MAKE) docker-status

docker-down: ## 停止并删除 Docker 服务
	@echo "$(BLUE)🛑 停止 Docker 服务...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Docker 服务已停止$(NC)"

docker-restart: ## 重启 Docker 服务
	@echo "$(BLUE)🔄 重启 Docker 服务...$(NC)"
	$(DOCKER_COMPOSE) restart
	@echo "$(GREEN)✅ Docker 服务已重启$(NC)"

docker-logs: ## 查看 Docker 服务日志
	@echo "$(BLUE)📋 查看服务日志...$(NC)"
	$(DOCKER_COMPOSE) logs -f

docker-logs-api: ## 查看 API 服务日志
	@echo "$(BLUE)📋 查看 API 服务日志...$(NC)"
	$(DOCKER_COMPOSE) logs -f api

docker-logs-scheduler: ## 查看调度器日志
	@echo "$(BLUE)📋 查看调度器日志...$(NC)"
	$(DOCKER_COMPOSE) logs -f scheduler

docker-status: ## 查看 Docker 服务状态
	@echo "$(BLUE)📊 Docker 服务状态:$(NC)"
	@$(DOCKER_COMPOSE) ps
	@echo ""

docker-rebuild: ## 重新构建并启动 Docker 服务
	@echo "$(BLUE)🔨 重新构建 Docker 镜像...$(NC)"
	$(DOCKER_COMPOSE) up -d --build
	@echo "$(GREEN)✅ Docker 服务已重新构建并启动$(NC)"

##@ 测试

test-health: ## 测试健康检查接口
	@echo "$(BLUE)🧪 测试健康检查...$(NC)"
	@curl -s http://localhost:9000/health | $(PYTHON) -m json.tool && echo "$(GREEN)✅ 健康检查通过$(NC)" || echo "$(RED)❌ 健康检查失败$(NC)"

test-callback: ## 测试审批回调接口
	@echo "$(BLUE)🧪 测试审批回调...$(NC)"
	@curl -s -X POST 'http://localhost:9000/feishu/approval/callback' \
		-H 'Content-Type: application/json' \
		-d '{"type":"url_verification","challenge":"test123"}' | $(PYTHON) -m json.tool && \
		echo "$(GREEN)✅ 回调测试通过$(NC)" || echo "$(RED)❌ 回调测试失败$(NC)"

test-approval: ## 运行审批功能测试脚本
	@echo "$(BLUE)🧪 运行审批功能测试...$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) playground/test_approval.py

test-setup: ## 运行配置检查脚本
	@echo "$(BLUE)🧪 运行配置检查...$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) playground/check_approval_setup.py

test-bitable: ## 测试多维表格接口
	@echo "$(BLUE)🧪 测试多维表格...$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) playground/test_bitable.py

test-labor: ## 运行工时检查测试
	@echo "$(BLUE)🧪 运行工时检查...$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) playground/run_labor_hour_check.py

test-week-summary: ## 运行周报测试
	@echo "$(BLUE)🧪 运行周报测试...$(NC)"
	@cd $(BACKEND_DIR) && $(PYTHON) playground/run_week_summary.py

test-all: ## 运行所有测试
	@$(MAKE) test-health
	@echo ""
	@$(MAKE) test-callback
	@echo ""
	@$(MAKE) test-setup

##@ 配置管理

config-show: ## 显示当前配置（隐藏敏感信息）
	@echo "$(BLUE)⚙️  当前配置:$(NC)"
	@echo ""
	@echo "$(BLUE)1. Labor Hour 配置:$(NC)"
	@if [ -f "$(BACKEND_DIR)/src/config/labor_hour.json" ]; then \
		cat $(BACKEND_DIR)/src/config/labor_hour.json | $(PYTHON) -c "import sys, json; data=json.load(sys.stdin); data['feishu']['app_secret']='***'; data['webhook']['secret']='***' if data['webhook']['secret'] else ''; print(json.dumps(data, indent=2, ensure_ascii=False))"; \
	else \
		echo "  $(RED)配置文件不存在$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)2. 人员配置:$(NC)"
	@if [ -f "$(BACKEND_DIR)/src/config/people.json" ]; then \
		cat $(BACKEND_DIR)/src/config/people.json | $(PYTHON) -m json.tool; \
	else \
		echo "  $(RED)配置文件不存在$(NC)"; \
	fi

config-edit-labor: ## 编辑工时配置文件
	@$$EDITOR $(BACKEND_DIR)/src/config/labor_hour.json

config-edit-people: ## 编辑人员配置文件
	@$$EDITOR $(BACKEND_DIR)/src/config/people.json

config-edit-tasks: ## 编辑定时任务配置文件
	@$$EDITOR $(BACKEND_DIR)/src/config/scheduled_tasks.json

##@ 清理

clean: ## 清理临时文件和缓存
	@echo "$(BLUE)🧹 清理临时文件...$(NC)"
	@find $(PROJECT_ROOT) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find $(PROJECT_ROOT) -type f -name "*.pyc" -delete 2>/dev/null || true
	@find $(PROJECT_ROOT) -type f -name "*.pyo" -delete 2>/dev/null || true
	@find $(PROJECT_ROOT) -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ 清理完成$(NC)"

clean-logs: ## 清理 Docker 日志
	@echo "$(BLUE)🧹 清理 Docker 日志...$(NC)"
	@rm -rf docker/logs/*
	@echo "$(GREEN)✅ 日志清理完成$(NC)"

##@ Git 操作

git-status: ## 查看 Git 状态
	@git status

git-log: ## 查看最近的 Git 提交
	@git log --oneline -10

git-push: ## 推送到远程仓库
	@echo "$(BLUE)📤 推送到远程仓库...$(NC)"
	@git push
	@echo "$(GREEN)✅ 推送完成$(NC)"

##@ 快速操作

dev: check install run ## 开发环境：检查配置 → 安装依赖 → 启动服务

deploy: docker-down docker-rebuild docker-status ## 部署：停止 → 重建 → 启动 → 查看状态

quick-test: docker-restart test-health test-callback ## 快速测试：重启服务 → 测试健康检查 → 测试回调

restart: ## 重启服务（自动检测 Docker 或本地）
	@if $(DOCKER_COMPOSE) ps | grep -q "agent2im-api"; then \
		echo "$(BLUE)🔄 重启 Docker 服务...$(NC)"; \
		$(DOCKER_COMPOSE) restart; \
	else \
		echo "$(YELLOW)⚠️  Docker 服务未运行，请使用 'make run' 启动本地服务$(NC)"; \
	fi

logs: ## 查看日志（自动检测 Docker 或本地）
	@if $(DOCKER_COMPOSE) ps | grep -q "agent2im-api"; then \
		$(MAKE) docker-logs-api; \
	else \
		echo "$(YELLOW)⚠️  Docker 服务未运行$(NC)"; \
	fi

##@ 信息

info: ## 显示项目信息
	@echo ""
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║           Agent2IM - HR 小助手                              ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)📁 项目路径:$(NC) $(PROJECT_ROOT)"
	@echo "$(GREEN)🐍 Python 路径:$(NC) $(PYTHONPATH)"
	@echo ""
	@echo "$(GREEN)🌐 服务地址:$(NC)"
	@echo "   API 服务:    http://localhost:9000"
	@echo "   API 文档:    http://localhost:9000/docs"
	@echo "   健康检查:    http://localhost:9000/health"
	@echo "   审批回调:    http://localhost:9000/feishu/approval/callback"
	@echo ""
	@echo "$(GREEN)📚 文档:$(NC)"
	@echo "   快速开始:    QUICKSTART_APPROVAL.md"
	@echo "   配置指南:    SETUP_HR_ASSISTANT.md"
	@echo "   部署指南:    DEPLOYMENT_GUIDE.md"
	@echo "   检查清单:    DEPLOY_CHECKLIST.md"
	@echo ""
	@echo "$(GREEN)💡 快速命令:$(NC)"
	@echo "   make dev              开发环境一键启动"
	@echo "   make deploy           Docker 部署"
	@echo "   make quick-test       快速测试"
	@echo "   make help             查看所有命令"
	@echo ""

version: ## 显示版本信息
	@echo "$(BLUE)Agent2IM v1.0.0$(NC)"
	@echo "Python: $$($(PYTHON) --version)"
	@if [ -n "$(CONDA_ENV)" ]; then \
		echo "Conda: $$(conda --version)"; \
		echo "Conda Env: $(CONDA_ENV)"; \
	fi
	@echo "Docker: $$(docker --version 2>/dev/null || echo 'Not installed')"
	@echo "Git: $$(git --version)"

