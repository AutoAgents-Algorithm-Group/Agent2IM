FROM python:3.11-slim

# 构建参数：服务类型 (api 或 scheduler)
ARG SERVICE_TYPE=api

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# 设置时区为东八区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制requirements.txt并安装依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY backend/ ./backend/

# 复制启动脚本（根据服务类型）
COPY docker/start.sh ./start.sh
COPY docker/schedule.sh ./schedule.sh
RUN chmod +x start.sh schedule.sh

# 设置环境变量
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1
ENV SERVICE_TYPE=${SERVICE_TYPE}

# 创建日志目录
RUN mkdir -p /app/logs

# 条件暴露端口（仅 API 服务需要）
EXPOSE 9000

# 健康检查（根据服务类型）
# API: 检查 HTTP 端点
# Scheduler: 检查进程
HEALTHCHECK --interval=60s --timeout=10s --start-period=40s --retries=3 \
    CMD if [ "$SERVICE_TYPE" = "api" ]; then \
            curl -f http://localhost:9000/health || exit 1; \
        else \
            pgrep -f "unified_scheduler" || exit 1; \
        fi

# 启动应用（根据服务类型选择不同的启动脚本）
CMD if [ "$SERVICE_TYPE" = "scheduler" ]; then \
        /app/schedule.sh; \
    else \
        /app/start.sh; \
    fi
